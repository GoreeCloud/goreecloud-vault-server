//! Fail-closed lifecycle readiness for the native `GoreeCloud` Vault Server.
//!
//! These gates describe integration and acceptance state, not runtime secrets.
//! A green source build does not make any gate ready automatically.

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct Gate {
    pub name: &'static str,
    pub ready: bool,
}

pub const NATIVE_FOUNDATION: Gate = Gate {
    name: "native_foundation",
    ready: true,
};

pub const REQUIRED_PRODUCTION_GATES: &[Gate] = &[
    Gate {
        name: "goreecloud_identity",
        ready: false,
    },
    Gate {
        name: "persistent_store",
        ready: false,
    },
    Gate {
        name: "goreecloud_mesh",
        ready: false,
    },
    Gate {
        name: "glaze_ui",
        ready: false,
    },
    Gate {
        name: "wardveil_security",
        ready: false,
    },
    Gate {
        name: "privacy_shield",
        ready: false,
    },
    Gate {
        name: "everkeep",
        ready: false,
    },
    Gate {
        name: "real_supported_clients",
        ready: false,
    },
    Gate {
        name: "webauthn_passkey_acceptance",
        ready: false,
    },
    Gate {
        name: "migration_rollback_acceptance",
        ready: false,
    },
    Gate {
        name: "repository_release_governance",
        ready: false,
    },
    Gate {
        name: "target_environment_acceptance",
        ready: false,
    },
    Gate {
        name: "production_approval",
        ready: false,
    },
];

#[must_use]
pub fn production_ready() -> bool {
    REQUIRED_PRODUCTION_GATES.iter().all(|gate| gate.ready)
}

#[must_use]
pub fn blocked_gate_names() -> Vec<&'static str> {
    REQUIRED_PRODUCTION_GATES
        .iter()
        .filter(|gate| !gate.ready)
        .map(|gate| gate.name)
        .collect()
}

#[cfg(test)]
mod tests {
    use super::{blocked_gate_names, production_ready, NATIVE_FOUNDATION, REQUIRED_PRODUCTION_GATES};

    #[test]
    fn native_foundation_is_present_but_production_stays_fail_closed() {
        assert!(NATIVE_FOUNDATION.ready);
        assert!(!production_ready());
        assert_eq!(blocked_gate_names().len(), REQUIRED_PRODUCTION_GATES.len());
    }

    #[test]
    fn every_current_production_gate_is_explicitly_blocked() {
        assert!(REQUIRED_PRODUCTION_GATES.iter().all(|gate| !gate.ready));
        assert!(REQUIRED_PRODUCTION_GATES
            .iter()
            .any(|gate| gate.name == "privacy_shield"));
        assert!(REQUIRED_PRODUCTION_GATES
            .iter()
            .any(|gate| gate.name == "everkeep"));
    }
}
