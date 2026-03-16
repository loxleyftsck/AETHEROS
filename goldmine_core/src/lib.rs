use pyo3::prelude::*;
use std::collections::VecDeque;
use hashbrown::HashMap;

/// A high-performance Top-K Sliding Window memory using PyO3
#[pyclass]
struct TopKMemory {
    capacity: usize,
    items: VecDeque<String>,
    // frequency map for top-k elements
    frequencies: HashMap<String, usize>,
}

#[pymethods]
impl TopKMemory {
    #[new]
    fn new(capacity: usize) -> Self {
        TopKMemory {
            capacity,
            items: VecDeque::with_capacity(capacity),
            frequencies: HashMap::new(),
        }
    }

    fn push(&mut self, item: String) {
        if self.items.len() == self.capacity {
            if let Some(old) = self.items.pop_front() {
                if let Some(count) = self.frequencies.get_mut(&old) {
                    *count -= 1;
                    if *count == 0 {
                        self.frequencies.remove(&old);
                    }
                }
            }
        }
        *self.frequencies.entry(item.clone()).or_insert(0) += 1;
        self.items.push_back(item);
    }

    fn get_top_k(&self, k: usize) -> Vec<(String, usize)> {
        let mut vec: Vec<_> = self.frequencies.iter()
            .map(|(s, &c)| (s.clone(), c))
            .collect();
        vec.sort_by(|a, b| b.1.cmp(&a.1));
        vec.into_iter().take(k).collect()
    }
}

/// A highly optimized rules engine for immediate HFT constraint validation
#[pyclass]
struct HftRulesEngine {
    max_drawdown_pct: f64,
    kelly_cap_pct: f64,
}

#[pymethods]
impl HftRulesEngine {
    #[new]
    fn new(max_drawdown_pct: f64, kelly_cap_pct: f64) -> Self {
        HftRulesEngine {
            max_drawdown_pct,
            kelly_cap_pct,
        }
    }

    /// Evaluates if a trade is valid against strict thresholds
    fn validate_trade(&self, confidence: f64, rr_ratio: f64, market_fear_index: u32) -> bool {
        // Fast-fail constraints
        if confidence < 0.60 {
            return false; // Minimum 60% confidence
        }
        if rr_ratio < 1.5 {
            return false; // Minimum 1:1.5 Risk-Reward
        }
        if market_fear_index > 85 {
            return false; // Extreme panic overrides
        }
        true
    }

    fn get_kelly_fraction(&self, win_prob: f64, rr_ratio: f64) -> f64 {
        let fraction = win_prob - ((1.0 - win_prob) / rr_ratio);
        // Cap the max risk
        if fraction > self.kelly_cap_pct {
            self.kelly_cap_pct
        } else if fraction < 0.0 {
            0.0
        } else {
            fraction
        }
    }
}

/// The Python module wrapper
#[pymodule]
fn goldmine_core(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_class::<TopKMemory>()?;
    m.add_class::<HftRulesEngine>()?;
    Ok(())
}
