CREATE TABLE form (
    id INT AUTO_INCREMENT PRIMARY KEY,
    CertificateNumber VARCHAR(255),
    date DATE,
    applicant_name VARCHAR(255),
    container_number VARCHAR(255),
    size_type VARCHAR(255),
    tare_weight VARCHAR(255),
    payload_capacity VARCHAR(255),
    declared_total_weight VARCHAR(255),
    stuffing_comm_date_time DATETIME,
    stuffing_comp_date_time DATETIME,
    seal_number VARCHAR(255),
    port_of_discharge VARCHAR(255),
    place_of_stuffing VARCHAR(255),
    cbm VARCHAR(255),
    loading_condition TEXT,
    lashing TEXT,
    others TEXT,
    weather_condition VARCHAR(50),
    surveyor_name VARCHAR(255),
    signature VARCHAR(255),
    consignment_details JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);