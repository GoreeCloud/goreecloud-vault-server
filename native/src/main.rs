use std::env;
use std::process::ExitCode;

use goreecloud_vault_native::readiness::{
    NATIVE_FOUNDATION, REQUIRED_PRODUCTION_GATES, blocked_gate_names, production_ready,
};

fn main() -> ExitCode {
    let command = env::args().nth(1);
    match command.as_deref() {
        Some("status") => {
            print_status();
            ExitCode::SUCCESS
        }
        Some("ready") => {
            if production_ready() {
                println!("production_ready=true");
                ExitCode::SUCCESS
            } else {
                eprintln!("production_ready=false");
                ExitCode::FAILURE
            }
        }
        Some("help" | "--help" | "-h") | None => {
            print_help();
            ExitCode::SUCCESS
        }
        Some(_) => {
            eprintln!("unknown command; use 'status', 'ready', or 'help'");
            ExitCode::from(2)
        }
    }
}

fn print_status() {
    println!("{}={}", NATIVE_FOUNDATION.name, NATIVE_FOUNDATION.ready);
    for gate in REQUIRED_PRODUCTION_GATES {
        println!("{}={}", gate.name, gate.ready);
    }
    println!("blocked_gate_count={}", blocked_gate_names().len());
    println!("production_ready={}", production_ready());
}

fn print_help() {
    println!("GoreeCloud Vault Server native development foundation");
    println!("usage: goreecloud-vault-native [status|ready|help]");
    println!("status prints bounded non-sensitive lifecycle state");
    println!("ready exits unsuccessfully until every production gate is accepted");
}
