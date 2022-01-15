CREATE TABLE IF NOT EXISTS users
(
    id bigserial PRIMARY KEY,
    telegram_id bigint NOT NULL,
    username varchar(256) NOT NULL,
    first_name varchar(256) NOT NULL,
    last_name varchar(256),
    is_owner boolean,
    beta_access boolean,
    welcome_message boolean
);
ALTER TABLE IF EXISTS public.users
    OWNER to sgotgbot;
CREATE TABLE IF NOT EXISTS accounts
(
    id bigserial PRIMARY KEY,
    telegram_id bigint NOT NULL,
    cid bigint NOT NULL,
    sid bigint NOT NULL,
    pid bigint NOT NULL,
    cn bigint NOT NULL,
    sft bigint NOT NULL,
    scid bigint NOT NULL,
    login varchar(256) NOT NULL,
    password varchar(256) NOT NULL,
    url varchar(256) NOT NULL,
    status varchar(256),
    display_name varchar(256),
    school_name varchar(256),
    class_name varchar(256),
    chat_id bigint,
    alert boolean
);
ALTER TABLE IF EXISTS public.accounts
    OWNER to sgotgbot;
CREATE TABLE IF NOT EXISTS regions
(
    id bigserial PRIMARY KEY,
    display_name varchar(256) NOT NULL,
    url varchar(256) NOT NULL,
    users_count bigint NOT NULL DEFAULT 0
);
ALTER TABLE IF EXISTS public.regions
    OWNER to sgotgbot;