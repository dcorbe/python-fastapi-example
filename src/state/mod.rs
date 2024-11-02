use std::collections::HashMap;
use std::sync::{Arc, Mutex};

// This application needs to keep a JWT secret key.
// WARNING: This is sensitive information.
#[derive(Clone)]
pub struct AppState {
    jwt_secret: Option<Arc<String>>,
    token_blacklist: Arc<Mutex<HashMap<String, i64>>>,
}

#[derive(Debug, thiserror::Error)]
pub enum Error {
    #[error("JWT secret is required")]
    MissingJwtSecret,
}


impl AppState {
    pub fn new() -> Self {
        Self {
            jwt_secret: None,
            token_blacklist: Arc::new(Mutex::new(HashMap::new())),
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
}
