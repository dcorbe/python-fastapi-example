use std::collections::HashMap;
use std::sync::{Arc, Mutex};
use core::time::Duration;
use sqlx::PgPool;
use sqlx::postgres::{PgPoolOptions};

// This application needs to keep a JWT secret key.
// WARNING: This is sensitive information.
#[derive(Clone, Debug)]
pub struct AppState {
    jwt_secret: Option<Arc<String>>,
    token_blacklist: Arc<Mutex<HashMap<String, i64>>>,
    pool: Option<Arc<PgPool>>,
    uri: Option<Arc<String>>,
}

#[derive(Debug, thiserror::Error)]
pub enum Error {
    #[error("JWT secret is required")]
    MissingJwtSecret,
    #[error("Database error: {0}")]
    DatabaseError(#[from] sqlx::Error),  // This #[from] attribute is important
    #[error("Database connection not initialized")]
    DatabaseNotInitialized,
}

impl AppState {
    pub fn new() -> Self {
        Self {
            jwt_secret: None,
            token_blacklist: Arc::new(Mutex::new(HashMap::new())),
            pool: None,
            uri: None,
        }
    }

    pub fn with_jwt_secret(mut self, jwt_secret: Arc<String>) -> Self {
        self.jwt_secret = Some(jwt_secret);
        self
    }

    pub fn jwt_secret(&self) -> Result<&Arc<String>, Error> {
        match &self.jwt_secret {
            Some(secret) => Ok(secret),
            None => Err(Error::MissingJwtSecret),
        }
    }

    pub fn token_blacklist(&self) -> &Arc<Mutex<HashMap<String, i64>>> {
        &self.token_blacklist
    }

    pub async fn with_db_uri(mut self, uri: String) -> Result<Self, Error> {
        self.uri = Some(Arc::new(uri.clone()));

        // Configure connection pool
        let pool = PgPoolOptions::new()
            .min_connections(5)
            .max_connections(100)
            .acquire_timeout(Duration::from_secs(3))
            .idle_timeout(Duration::from_secs(600))
            .connect(&uri)
            .await
            .map_err(|e| Error::DatabaseError(e))?;

        // Test the connection to ensure it works
        pool.acquire()
            .await
            .map_err(|e| Error::DatabaseError(e))?;

        // Store the pool in the state
        self.pool = Some(Arc::new(pool));

        /* Let's try and connect to the database right away */
        Ok(self)
    }

    pub fn db(&self) -> Result<&PgPool, Error> {
        self.pool
            .as_deref()
            .ok_or(Error::DatabaseNotInitialized)
    }
}
