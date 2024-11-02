use axum::{Json};
use serde_json::{Value};

pub async fn handle_ping(
    Json(body): Json<Value>,
) -> Json<Value> {
    Json::from(body)
}
