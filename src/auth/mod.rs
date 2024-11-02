use axum::extract::State;
use axum::http::StatusCode;
use axum::Json;
use chrono::{Duration, Utc};
use jsonwebtoken::{encode, decode, EncodingKey, DecodingKey, Header, Validation};
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use crate::AppState;

// This is a JWT claim.
#[derive(Debug, Serialize, Deserialize)]
struct Claims {
    sub: String,     // Subject (user ID)
    exp: i64,        // Expiration time
    iat: i64,        // Issued at time
}

#[derive(Deserialize, Debug)]
pub struct LoginRequest {
    username: String,
    password: String,
}

#[derive(Serialize)]
pub struct LoginResponse {
    token: String,
    token_type: String,
}


#[derive(Debug, thiserror::Error)]
pub enum Error {
    #[error("Invalid credentials")]
    InvalidCredentials,
    #[error("Token creation failed")]
    TokenCreation,
    #[error("Token validation failed")]
    TokenValidation,
}

impl From<Error> for (StatusCode, Json<Value>) {
    fn from(error: Error) -> Self {
        let status = match &error {
            Error::InvalidCredentials => StatusCode::UNAUTHORIZED,
            Error::TokenCreation | Error::TokenValidation => StatusCode::INTERNAL_SERVER_ERROR,
            _ => StatusCode::INTERNAL_SERVER_ERROR,
        };
        (status, Json(json!({ "error": error.to_string() })))
    }
}


struct Session {
    state: AppState,
    claim: Option<Claims>
}

impl Session {
    pub fn new(state: AppState) -> Self {
        Self {
            state,
            claim: None
        }
    }

    pub async fn login(&self, credentials: LoginRequest) -> Result<LoginResponse, Error> {
        // TODO: Replace with actual database lookup and password verification
        if credentials.username == "admin" && credentials.password == "password" {
            let token = self.create_token(credentials.username)?;

            Ok(LoginResponse {
                token,
                token_type: "Bearer".to_string(),
            })
        } else {
            Err(Error::InvalidCredentials)
        }
    }

    pub fn create_token(&self, user_id: String) -> Result<String, Error> {
        let now = Utc::now();
        let expires_at = now + Duration::hours(1);

        let claims = Claims {
            sub: user_id,
            exp: expires_at.timestamp(),
            iat: now.timestamp(),
        };

        encode(
            &Header::default(),
            &claims,
            &EncodingKey::from_secret(self.state.jwt_secret.as_bytes()),
        )
            .map_err(|_| Error::TokenCreation)
    }

    // Verify a JWT token
    pub fn verify_token(&self, token: &str) -> Result<Claims, Error> {
        let validation = Validation::default();
        decode::<Claims>(
            token,
            &DecodingKey::from_secret(self.state.jwt_secret.as_bytes()),
            &validation,
        )
            .map(|data| data.claims)
            .map_err(|_| Error::TokenValidation)
    }
}

pub async fn handle_login(
    State(state): State<AppState>,
    Json(login_req): Json<LoginRequest>,
) -> Result<Json<LoginResponse>, (StatusCode, Json<Value>)> {
    let session = Session::new(state);
    session.login(login_req)
        .await
        .map(Json)
        .map_err(Into::into)
}
