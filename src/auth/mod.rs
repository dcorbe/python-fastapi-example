use axum::extract::State;
use axum::http::StatusCode;
use axum::Json;
use chrono::{Duration, Utc};
use jsonwebtoken::{encode, EncodingKey, Header};
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

struct Session {
}

impl Session {
    pub fn new(state: AppState) -> Self {
        Self { }
    }

    // Generate a new JWT token
}
#[derive(Serialize)]
pub struct LoginResponse {
    token: String,
    token_type: String,
}

pub async fn login(
    State(state): State<AppState>,
    Json(login_req): Json<LoginRequest>
) -> Result<Json<LoginResponse>, (StatusCode, Json<Value>)> {
    println!("Login request: {:?}", login_req);
    // TODO: This would be a great place to start doing DB work.
    if login_req.username == "admin" && login_req.password == "password" {
        let now = Utc::now();
        let expires_at = now + Duration::hours(1);

        let claims = Claims {
            sub: login_req.username,
            exp: expires_at.timestamp(),
            iat: now.timestamp(),
        };

        // Generate the token
        let token = encode(
            &Header::default(),
            &claims,
            &EncodingKey::from_secret(state.jwt_secret.as_ref())
        ).map_err(|_| (
            StatusCode::INTERNAL_SERVER_ERROR,
            Json(json!({ "error": "Failed to create token" }))
        ))?;

        Ok(Json(LoginResponse {
            token,
            token_type: "Bearer".to_string(),
        }))
    } else {
        Err((
            StatusCode::UNAUTHORIZED,
            Json(json!({ "error": "Invalid credentials" }))
        ))
    }
}
