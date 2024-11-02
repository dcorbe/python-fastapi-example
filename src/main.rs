use std::collections::HashMap;

use axum::{
    routing::{post, get},
    Router,
    response::Json,
    extract::Extension,
};

use axum::middleware::from_fn_with_state;
use serde_json::{Value, json};
use serde::{Serialize, Deserialize};
use tower_http::cors::CorsLayer;
use std::sync::{Arc, Mutex};

mod auth;
use auth::{Claims, handle_login, handle_logout};

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    //TODO: Here is where you'll either want to load or generate a secret key for JWT.
    let state = AppState {
        jwt_secret: Arc::new("your-secret-key-here".to_string()), // FIXME: In production, load from env
        token_blacklist: Arc::new(Mutex::new(HashMap::new())),
    };

    let public_routes = Router::new()
        .route("/login", post(handle_login))
        .route("/logout", get(handle_logout));

    let protected_routes = Router::new()
        .route("/api", post(api))
        .layer(from_fn_with_state(
            state.clone(),
            auth::auth_middleware,
        ));

    // This maps incoming URLs to the functions that will handle them.
    let app = Router::new()
        .merge(public_routes)
        .merge(protected_routes)
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
    user: String,
}

// This is an example of a protected endpoint
async fn api(
    Extension(claims): Extension<Claims>,
    Json(body): Json<Value>,
) -> Json<Testing> {
    let name = body["name"].as_str().unwrap();
    let response = Testing {
        name: name.to_string(),
        user: claims.sub().to_string(),
    };
    Json(response)
}

// This application needs to keep a JWT secret key.
// WARNING: This is sensitive information.
#[derive(Clone)]
struct AppState {
    jwt_secret: Arc<String>,
    token_blacklist: Arc<Mutex<HashMap<String, i64>>>,
}
