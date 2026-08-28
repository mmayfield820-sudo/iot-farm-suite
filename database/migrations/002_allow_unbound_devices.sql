USE smart_agriculture;

ALTER TABLE devices
    MODIFY COLUMN plot_id BIGINT UNSIGNED NULL;