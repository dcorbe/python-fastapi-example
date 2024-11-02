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
use std::sync::Arc;

mod auth;

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    //TODO: Here is where you'll either want to load or generate a secret key for JWT.
    let state = AppState {
        jwt_secret: "your-secret-key-here".to_string(), // In production, load from env
    };

    // This maps incoming URLs to the functions that will handle them.
    let app = Router::new()
        .route("/api", post(api))
        .route("/login", post(auth::handle_login))
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

// This application needs to keep a JWT secret key.
// WARNING: This is sensitive information.
#[derive(Clone)]
struct AppState {
    jwt_secret: String,
}
