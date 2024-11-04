use std::env;
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
use std::sync::{Arc};

use bss_backend::auth::{Claims, handle_login, handle_logout};
use bss_backend::state::AppState;
use bss_backend::ping::handle_ping;


#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let state = AppState::new()
        .with_jwt_secret(Arc::new(
            env::var("JWT_SECRET").expect("JWT_SECRET must be set")))
        .with_db_uri(
            env::var("DATABASE_URL").expect("DATABASE_URL must be set"))
        .await?;

    let public_routes = Router::new()
        .route("/login", post(handle_login))
        .route("/logout", get(handle_logout));

    let protected_routes = Router::new()
        .route("/api", post(api))
        .route("/ping", post(handle_ping))
        .layer(from_fn_with_state(
            state.clone(),
            bss_backend::auth::middleware,
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
    let name = body["name"].as_str().unwrap();  // FIXME: This WILL panic if the key is missing
    let response = Testing {
        name: name.to_string(),
        user: claims.sub().to_string(),
    };
    Json(response)
}
