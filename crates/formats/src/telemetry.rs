//! # Telemetry
//!
//! This is a collection of structs defining telemetry
//! interchange formats used across the entire project.

use serde::{Deserialize, Serialize};

/// Speeeeeeeeeed
#[derive(Serialize, Deserialize, Debug, Eq, PartialEq)]
pub struct Speeeeeeeeeed {
    /// Velocity is represented in m/s
    pub velocity: i32,
    /// Acceleration is represented in cm/s²
    pub acceleration: i32,
}
