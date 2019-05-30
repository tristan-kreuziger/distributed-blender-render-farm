
CREATE TABLE render_project
(
	id INT AUTO_INCREMENT,
	project_name VARCHAR(100) NOT NULL,
	filename VARCHAR(100) NOT NULL,
	number_of_frames INT NOT NULL,
	CONSTRAINT render_project_pk
		PRIMARY KEY (id)
);

CREATE UNIQUE INDEX render_project_project_name_uindex
	ON render_project (project_name);

CREATE TABLE render_project_status
(
	id INT AUTO_INCREMENT,
	status_name VARCHAR(30) NOT NULL,
	CONSTRAINT render_project_status_pk
		PRIMARY KEY (id)
);

CREATE UNIQUE INDEX render_project_status_status_name_uindex
	ON render_project_status (status_name);

INSERT INTO render_project_status (status_name) VALUES
  ('CREATED'), ('RUNNING'), ('FINISHED'), ('CANCELLED');

CREATE TABLE render_project_history
(
	render_project_id INT NOT NULL,
	change_date DATETIME NOT NULL,
	status INT NOT NULL,
	CONSTRAINT render_project_history_pk
		PRIMARY KEY (render_project_id, change_date),
	CONSTRAINT render_project_history_render_project_id_fk
		FOREIGN KEY (render_project_id) REFERENCES render_project (id)
			ON UPDATE CASCADE ON DELETE CASCADE
);

CREATE TABLE render_machine
(
	id INT AUTO_INCREMENT,
	machine_name VARCHAR(50) NOT NULL,
	CONSTRAINT render_machine_pk
		PRIMARY KEY (id)
);

CREATE UNIQUE INDEX render_machine_machine_name_uindex
	ON render_machine (machine_name);

INSERT INTO render_machine (machine_name) VALUES ('SERVER');

CREATE TABLE frame_task
(
	render_project_id INT NOT NULL,
	frame_index INT NOT NULL,
	CONSTRAINT frame_task_pk
		PRIMARY KEY (render_project_id, frame_index),
	CONSTRAINT frame_task_render_project_id_fk
		FOREIGN KEY (render_project_id) REFERENCES render_project (id)
			ON UPDATE CASCADE ON DELETE CASCADE
);

CREATE TABLE frame_task_status
(
	id INT AUTO_INCREMENT,
	status_name VARCHAR(30) NOT NULL,
	CONSTRAINT frame_task_status_pk
		PRIMARY KEY (id)
);

CREATE UNIQUE INDEX frame_task_status_status_name_uindex
	ON frame_task_status (status_name);

INSERT INTO frame_task_status (status_name) VALUES
	('CREATED'), ('RESERVED'), ('FINISHED'), ('CANCELLED'), ('FAILED');

CREATE TABLE frame_task_history
(
	render_project_id INT NOT NULL,
	frame_index INT NOT NULL,
	change_date DATETIME NOT NULL,
	machine_id INT NULL,
	status INT NOT NULL,
	CONSTRAINT frame_task_history_pk
		PRIMARY KEY (render_project_id, frame_index, change_date),
	CONSTRAINT frame_task_history_frame_task_status_id_fk
		FOREIGN KEY (status) REFERENCES frame_task_status (id)
			ON UPDATE CASCADE ON DELETE CASCADE,
	CONSTRAINT frame_task_history_render_machine_id_fk
		FOREIGN KEY (machine_id) REFERENCES render_machine (id)
			ON UPDATE CASCADE ON DELETE CASCADE,
	CONSTRAINT frame_task_history_render_project_id_fk
		FOREIGN KEY (render_project_id) REFERENCES render_project (id)
			ON UPDATE CASCADE ON DELETE CASCADE
);

CREATE UNIQUE INDEX task_history_render_project_id_frame_index_change_date_uindex
	ON frame_task_history (render_project_id, frame_index, change_date);
