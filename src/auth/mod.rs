use axum::body::Body;
use axum::extract::State;
use axum::http::{Request, Response, StatusCode, header::AUTHORIZATION};
use axum::Json;
use axum::middleware::Next;
use chrono::{Duration, Utc};
use jsonwebtoken::{encode, decode, EncodingKey, DecodingKey, Header, Validation};
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use crate::AppState;

// This is a JWT claim.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Claims {
    sub: String,     // Subject (user ID)
    exp: i64,        // Expiration time
    iat: i64,        // Issued at time
}

impl Claims {
    pub fn new(sub: String, exp: i64, iat: i64) -> Self {
        Self { sub, exp, iat }
    }

    pub fn sub(&self) -> &str {
        &self.sub
    }

    pub fn exp(&self) -> i64 {
        self.exp
    }

    pub fn iat(&self) -> i64 {
        self.iat
    }
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
    token_expires: i64,
}


#[derive(Debug, thiserror::Error)]
pub enum Error {
    #[error("Invalid credentials")]
    InvalidCredentials,
    #[error("Token creation failed")]
    TokenCreation,
    #[error("Token validation failed")]
    TokenValidation,
    #[error("Token has expired")]
    TokenExpired,
    #[error("Invalid token format")]
    InvalidTokenFormat,

}

impl From<Error> for (StatusCode, Json<Value>) {
    fn from(error: Error) -> Self {
        let status = match &error {
            Error::InvalidCredentials | Error::TokenExpired => StatusCode::UNAUTHORIZED,
            Error::TokenCreation | Error::TokenValidation => StatusCode::INTERNAL_SERVER_ERROR,
            Error::InvalidTokenFormat => StatusCode::BAD_REQUEST,
        };
        (status, Json(json!({
            "error": error.to_string(),
            "code": match &error {
                Error::TokenExpired => "token_expired",
                Error::InvalidCredentials => "invalid_credentials",
                Error::TokenValidation => "token_invalid",
                Error::TokenCreation => "token_creation_failed",
                Error::InvalidTokenFormat => "invalid_format",
            }
        })))
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
            let (token, expires_at) = self.create_token(credentials.username)?;

            Ok(LoginResponse {
                token,
                token_type: "Bearer".to_string(),
                token_expires: expires_at,
            })
        } else {
            Err(Error::InvalidCredentials)
        }
    }

    pub fn create_token(&self, user_id: String) -> Result<(String, i64), Error> {
        let now = Utc::now();
        let expires_at = now + Duration::hours(1);

        let claims = Claims {
            sub: user_id,
            exp: expires_at.timestamp(),
            iat: now.timestamp(),
        };

        let token = encode(
            &Header::default(),
            &claims,
            &EncodingKey::from_secret(self.state.jwt_secret.as_bytes()),
        )
            .map_err(|_| Error::TokenCreation)?;
        Ok((token, expires_at.timestamp()))
    }

    // Verify a JWT token
    pub fn verify_token(&self, token: &str) -> Result<Claims, Error> {
        let validation = Validation::default();
        match decode::<Claims>(
            token,
            &DecodingKey::from_secret(self.state.jwt_secret.as_bytes()),
            &validation,
        ) {
            Ok(token_data) => {
                let claims = token_data.claims;

                // Explicit expiration check
                if claims.exp < Utc::now().timestamp() {
                    return Err(Error::TokenExpired);
                }

                Ok(claims)
            }
            Err(e) => match e.kind() {
                jsonwebtoken::errors::ErrorKind::ExpiredSignature => Err(Error::TokenExpired),
                jsonwebtoken::errors::ErrorKind::InvalidToken => Err(Error::InvalidTokenFormat),
                _ => Err(Error::TokenValidation)
            }
        }
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

pub async fn auth_middleware(
    State(state): State<AppState>,
    mut req: Request<Body>,
    next: Next,
) -> Result<Response<Body>, (StatusCode, Json<Value>)> {
    // 1. Extract the Authorization header
    let auth_header = req
        .headers()
        .get(AUTHORIZATION)
        .and_then(|header| header.to_str().ok())
        .ok_or_else(|| (
            StatusCode::UNAUTHORIZED,
            Json(json!({ "error": "Missing authorization header" }))
        ))?;

    // 2. Validate the header format
    if !auth_header.starts_with("Bearer ") {
        return Err((
            StatusCode::UNAUTHORIZED,
            Json(json!({ "error": "Invalid authorization header format" }))
        ));
    }

    // 3. Extract and verify the token
    let token = &auth_header[7..];
    let session = Session::new(state);
    let claims = session.verify_token(token)
        .map_err(|e: Error| { // Explicitly handle the error conversion
            let (status, json) = e.into();
            (status, json)
        })?;

    // 4. Store the verified claims for the route handler
    req.extensions_mut().insert(claims);

    // 5. Continue to the route handler
    Ok(next.run(req).await)
}
