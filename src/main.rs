use axum::{
    routing::{post, get},
    Router,
    response::Json,
    http::StatusCode,
    extract::State,
};
use serde_json::{Value, json};
use serde::{Serialize, Deserialize};
use jsonwebtoken::{encode, Header, EncodingKey};
use chrono::{Utc, Duration};
use tower_http::cors::CorsLayer;

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    //TODO: Here is where you'll either want to load or generate a secret key for JWT.
    let state = AppState {
        jwt_secret: "your-secret-key-here".to_string(), // In production, load from env
    };

    // This maps incoming URLs to the functions that will handle them.
    let app = Router::new()
        .route("/api", post(api))
        .route("/login", post(login))
        .layer(CorsLayer::permissive()) // FIXME: This is insecure, don't use permissive in production
        .with_state(state);

    // This will allow axum to service incoming requests in an infinite loop.
    let listener = tokio::net::TcpListener::bind("0.0.0.0:3000").await?;
    axum::serve(listener, app).await?;
    Ok(())
}

#[derive(Serialize)]
struct Testing {
    name: String,
}

async fn api(Json(body): Json<Value>) -> Json<Testing> {
    let name = body["name"].as_str().unwrap();
    let response = Testing {
        name: name.to_string(),
    };
    Json(response)
}

// This is a JWT claim.
#[derive(Debug, Serialize, Deserialize)]
struct Claims {
    sub: String,     // Subject (user ID)
    exp: i64,        // Expiration time
    iat: i64,        // Issued at time
}

// This application needs to keep a JWT secret key.
// WARNING: This is sensitive information.
#[derive(Clone)]
struct AppState {
    jwt_secret: String,
}

#[derive(Deserialize)]
struct LoginRequest {
    username: String,
    password: String,
}

#[derive(Serialize)]
struct LoginResponse {
    token: String,
    token_type: String,
}
async fn login(
    State(state): State<AppState>,
    Json(login_req): Json<LoginRequest>
) -> Result<Json<LoginResponse>, (StatusCode, Json<Value>)> {
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
