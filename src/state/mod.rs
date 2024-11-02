use std::collections::HashMap;
use std::sync::{Arc, Mutex};

// This application needs to keep a JWT secret key.
// WARNING: This is sensitive information.
#[derive(Clone)]
pub struct AppState {
    pub jwt_secret: Arc<String>,
    pub token_blacklist: Arc<Mutex<HashMap<String, i64>>>,
}

impl AppState {
    pub fn new(jwt_secret: String) -> Self {
        Self {
            jwt_secret: Arc::new(jwt_secret),
            token_blacklist: Arc::new(Mutex::new(HashMap::new())),
        }
    }

    pub fn jwt_secret(&self) -> &str {
        &self.jwt_secret
    }

    pub fn token_blacklist(&self) -> &Mutex<HashMap<String, i64>> {
        &self.token_blacklist
    }
}
