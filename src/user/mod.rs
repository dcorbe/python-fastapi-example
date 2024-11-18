use std::iter::Skip;
use axum::extract::State;
use chrono::{DateTime, Utc};
use uuid::Uuid;
use sqlx::PgPool;
use validator::ValidateEmail;
use crate::state::AppState;
use crate::state::Error::DatabaseError;

#[derive(Debug, sqlx::FromRow, Default, Clone)]
pub struct User {
    id: Option<Uuid>,
    email: Option<String>,
    password_hash: Option<String>,
    email_verified: bool,
    created_at: Option<DateTime<Utc>>,
    last_login: Option<DateTime<Utc>>,
    failed_login_attempts: i32,
    locked_until: Option<DateTime<Utc>>,
}

#[derive(Debug, thiserror::Error)]
pub enum Error {
    #[error("Validation Failed For User Object: {0}")]
    ValidationError(String),
    #[error("Email address is invalid: {0}")]
    EmailInvalid(#[from] validator::ValidationError),
    #[error("Email address is required")]
    EmailRequired,
    #[error("Database error: {0}")]
    DatabaseError(#[from] sqlx::Error),
    #[error("User not found")]
    UserNotFound,
}

impl From<crate::state::Error> for Error {
    fn from(error: crate::state::Error) -> Self {
        match error {
            crate::state::Error::DatabaseError(e) => Error::DatabaseError(e),
            // Handle other variants of `state::Error` if they exist
            _ => Error::ValidationError("Unknown state error".to_string()),
        }
    }
}

impl From<crate::state::Error> for sqlx::Error {
    fn from(err: crate::state::Error) -> Self {
        sqlx::Error::Protocol(err.to_string()) // Convert to a SQLx-compatible error
    }
}

#[derive(Debug)]
pub(crate) enum UserLookup {
    ByUuid(Uuid),
    ByEmail(String),
}

impl User {
    pub fn new() -> Self {
        Self {
            ..Default::default()
        }
    }

    pub fn with_uuid(mut self, id: Uuid) -> Self {
        self.id = Some(id);
        self
    }

    pub fn with_email(mut self, email: String) -> Self {
        self.email = Some(email);
        self
    }

    pub fn with_password_hash(mut self, password_hash: String) -> Self {
        self.password_hash = Some(password_hash);
        self
    }

    pub fn with_email_verified(mut self, email_verified: bool) -> Self {
        self.email_verified = email_verified;
        self
    }

    pub fn with_created_at(mut self, created_at: DateTime<Utc>) -> Self {
        self.created_at = Some(created_at);
        self
    }

    pub fn with_last_login(mut self, last_login: DateTime<Utc>) -> Self {
        self.last_login = Some(last_login);
        self
    }

    pub fn with_failed_login_attempts(mut self, failed_login_attempts: i32) -> Self {
        self.failed_login_attempts = failed_login_attempts;
        self
    }

    pub fn with_locked_until(mut self, locked_until: DateTime<Utc>) -> Self {
        self.locked_until = Some(locked_until);
        self
    }

    pub fn uuid(&self) -> Result<Uuid, Error> {
        match &self.id {
            Some(id) => Ok(*id),
            None => Err(Error::ValidationError("I have no UUID!".to_string())),
        }
    }

    pub fn email(&self) -> Result<&str, Error> {
        match &self.email {
            Some(email) => {
                if email.is_empty() {
                    Err(Error::EmailRequired)
                } else {
                    email.validate_email();  // Will automatically convert and propagate the error
                    Ok(email)
                }
            }
            None => Err(Error::EmailRequired),
        }
    }

    pub fn password_hash(&self) -> Result<&str, Error> {
        match &self.password_hash {
            Some(password_hash) => {
                if password_hash.is_empty() {
                    Err(Error::ValidationError("User has no password set!".to_string()))
                } else {
                    Ok(password_hash)
                }
            }
            None => Err(Error::ValidationError("User has no password set!".to_string())),
        }
    }

    pub fn email_verified(&self) -> bool {
        self.email_verified
    }

    pub fn created_at(&self) -> Result<DateTime<Utc>, Error> {
        match &self.created_at {
            Some(created_at) => Ok(*created_at),
            None => Err(Error::ValidationError("I have no created_at!".to_string())),
        }
    }

    pub fn last_login(&self) -> Result<DateTime<Utc>, Error> {
        match &self.last_login {
            Some(last_login) => Ok(*last_login),
            None => Ok(DateTime::from(DateTime::UNIX_EPOCH))
        }
    }

    pub fn failed_login_attempts(&self) -> i32 {
        self.failed_login_attempts
    }

    pub fn locked_until(&self) -> Result<DateTime<Utc>, Error> {
        match &self.locked_until {
            Some(locked_until) => Ok(*locked_until),
            None => Ok(DateTime::from(DateTime::UNIX_EPOCH)),
        }
    }

    pub async fn find_user(lookup: UserLookup, state: State<AppState>) -> Result<Self, Error> {
        match lookup {
            UserLookup::ByUuid(uuid) => {
                sqlx::query_as!(
                    User,
                    "SELECT id, email, password_hash, email_verified, created_at,
                            last_login, failed_login_attempts, locked_until
                    FROM users WHERE id = $1",
                    uuid
                )
                    .fetch_optional(state.db()?)
                    .await?
                    .ok_or(Error::UserNotFound)

            },
            UserLookup::ByEmail(email) => {
                sqlx::query_as!(
                    User,
                    "SELECT id, email, password_hash, email_verified, created_at,
                            last_login, failed_login_attempts, locked_until
                     FROM users WHERE LOWER(email) = LOWER($1)",
                    email
                )
                    .fetch_optional(state.db()?)
                    .await?.ok_or(Error::UserNotFound)
            }
        }
    }

    pub async fn create(
        email: &str,
        password_hash: &str,
        state: State<AppState>,
    ) -> Result<User, sqlx::Error> {
        let user = sqlx::query_as!(
            User,
            r#"
            INSERT INTO users (id, email, password_hash, email_verified, created_at, failed_login_attempts)
            VALUES ($1, $2, $3, false, NOW(), 0)
            RETURNING id, email, password_hash, email_verified, created_at, last_login, failed_login_attempts, locked_until
            "#,
            Uuid::new_v4(),
            email,
            password_hash
        )
            .fetch_one(state.db()?)
            .await?;

        Ok(user)
    }

    pub async fn delete(user_id: Uuid, state: State<AppState>) -> Result<(), sqlx::Error> {
        sqlx::query!(
            r#"
            DELETE FROM users WHERE id = $1
            "#,
            user_id
        )
            .execute(state.db()?)
            .await?;

        Ok(())
    }

    pub async fn save(
        user_id: Uuid,
        email: Option<&str>,
        password_hash: Option<&str>,
        state: State<AppState>,
    ) -> Result<User, sqlx::Error> {
        let user = sqlx::query_as!(
            User,
            r#"
            UPDATE users
            SET email = COALESCE($2, email),
                password_hash = COALESCE($3, password_hash),
                email_verified = false
            WHERE id = $1
            RETURNING id, email, password_hash, email_verified, created_at, last_login, failed_login_attempts, locked_until
            "#,
            user_id,
            email,
            password_hash
        )
            .fetch_one(state.db()?)
            .await?;

        Ok(user)
    }
}
