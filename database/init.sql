-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    full_name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT CHECK (role IN ('borrower', 'underwriter', 'admin')) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id),
    document_name TEXT NOT NULL,
    document_content BYTEA,
    document_type TEXT,
    parsed_data JSONB,
    uploaded_at TIMESTAMP DEFAULT NOW()
);
CREATE TABLE rule_evaluation_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id),
    document_id UUID REFERENCES documents(id),
    rule_values JSONB NOT NULL,  -- summary of all rule evaluations
    rule_status TEXT CHECK (rule_status IN ('pass', 'fail')) NOT NULL,
    evaluated_at TIMESTAMP DEFAULT NOW()
);
CREATE TABLE ml_prediction_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id),
    document_id UUID REFERENCES documents(id),
    predicted_decision TEXT CHECK (predicted_decision IN ('accepted', 'rejected')) NOT NULL,
    confidence_score FLOAT NOT NULL,
    shap_summary JSONB,
    evaluated_at TIMESTAMP DEFAULT NOW()
);
CREATE TABLE fairness_audit_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    ml_result_id UUID REFERENCES ml_prediction_results(id),
    bias_detected BOOLEAN NOT NULL,
    flagged_fields JSONB,
    audit_summary TEXT,
    audited_at TIMESTAMP DEFAULT NOW()
);
CREATE TABLE decision_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    type TEXT CHECK (type IN ('auto', 'override')) NOT NULL,
    borrower_id UUID REFERENCES users(id),
    underwriter_id UUID REFERENCES users(id),
    ml_result_id UUID REFERENCES ml_prediction_results(id),
    rule_result_id UUID REFERENCES rule_evaluation_log(id),
    fairness_audit_log_id UUID REFERENCES fairness_audit_log(id),
    final_decision TEXT CHECK (final_decision IN ('approved', 'rejected', 'pending', 'error', 'escalated')) NOT NULL,
    document_id UUID REFERENCES documents(id),
    explanation TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
CREATE TABLE shadow_model_feedback (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id),
    overridden_by UUID REFERENCES users(id),
    reason TEXT NOT NULL,
    model_gap_summary JSONB,  -- explainable factors or feature drift
    included_in_training BOOLEAN DEFAULT FALSE,
    recorded_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE rules_config (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    field TEXT NOT NULL,
    operator TEXT NOT NULL,  -- e.g., '>=', '<', '=', '!=', 'in', 'not in'
    value TEXT NOT NULL,     -- Stored as text, parsed based on field type
    message TEXT             -- Optional failure message
);

-- Sample Users
-- Password hash for 'password' using bcrypt
INSERT INTO users (full_name, email, password_hash, role)
VALUES 
  ('John Borrower', 'borrower1@example.com', '$2b$12$Z6c3pHL5zdaqlStD25Zp8.G7dkOknuDwRrgQUiVUpjCn9hpoLtMOK', 'borrower'),
  ('Jane Underwriter', 'underwriter1@example.com', '$2b$12$Z6c3pHL5zdaqlStD25Zp8.G7dkOknuDwRrgQUiVUpjCn9hpoLtMOK', 'underwriter');

INSERT INTO rules_config (name, field, operator, value, message) VALUES
('Salary Check', 'salary', '>=', '50000', 'Salary too low'),
('Employer Check', 'employer', 'not in', 'fraud inc, unknown corp', 'Blacklisted employer');