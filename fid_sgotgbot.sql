CREATE TABLE IF NOT EXISTS users
(
    id bigserial PRIMARY KEY,
    telegram_id bigint NOT NULL,
    first_name varchar(256),
    last_name varchar(256),
    username varchar(256),
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
    url varchar(256) NOT NULL,
    cid bigint,
    sid bigint,
    pid bigint,
    cn bigint,
    sft bigint,
    scid bigint,
    username varchar(256),
    password varchar(256),
    status varchar(256) DEFAULT 'register',
    display_name varchar(256),
    nickname varchar(256),
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