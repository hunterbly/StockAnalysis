--
-- PostgreSQL database dump
--

-- Dumped from database version 9.6.9
-- Dumped by pg_dump version 9.6.9

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: plpgsql; Type: EXTENSION; Schema: -; Owner: 
--

CREATE EXTENSION IF NOT EXISTS plpgsql WITH SCHEMA pg_catalog;


--
-- Name: EXTENSION plpgsql; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION plpgsql IS 'PL/pgSQL procedural language';


SET default_tablespace = '';

SET default_with_oids = false;

--
-- Name: ccass; Type: TABLE; Schema: public; Owner: root
--

CREATE TABLE public.ccass (
    id integer NOT NULL,
    participant_code character varying(20),
    participant character varying(150),
    number bigint,
    code character varying(10),
    date date,
    percentage numeric
);


ALTER TABLE public.ccass OWNER TO root;

--
-- Name: ccass_id_seq; Type: SEQUENCE; Schema: public; Owner: root
--

CREATE SEQUENCE public.ccass_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.ccass_id_seq OWNER TO root;

--
-- Name: ccass_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: root
--

ALTER SEQUENCE public.ccass_id_seq OWNED BY public.ccass.id;


--
-- Name: option; Type: TABLE; Schema: public; Owner: root
--

CREATE TABLE public.option (
    id integer NOT NULL,
    date date,
    code character varying(100),
    option_name character varying(200),
    option_desc character varying(200),
    option_date date,
    strike numeric,
    contract character varying(10),
    open numeric,
    high numeric,
    low numeric,
    settle numeric,
    delta_settle numeric,
    iv numeric,
    volume bigint,
    oi bigint,
    delta_oi bigint
);


ALTER TABLE public.option OWNER TO root;

--
-- Name: option_id_seq; Type: SEQUENCE; Schema: public; Owner: root
--

CREATE SEQUENCE public.option_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.option_id_seq OWNER TO root;

--
-- Name: option_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: root
--

ALTER SEQUENCE public.option_id_seq OWNED BY public.option.id;


--
-- Name: signal_hit; Type: TABLE; Schema: public; Owner: root
--

CREATE TABLE public.signal_hit (
    id integer NOT NULL,
    code character varying,
    date date,
    high_one double precision,
    high_two double precision,
    high_three double precision,
    high_four double precision,
    high_five double precision,
    low_one double precision,
    low_two double precision,
    low_three double precision,
    low_four double precision,
    low_five double precision,
    max_high double precision,
    min_low double precision,
    signal character varying,
    hit double precision
);


ALTER TABLE public.signal_hit OWNER TO root;

--
-- Name: signal_hit_id_seq; Type: SEQUENCE; Schema: public; Owner: root
--

CREATE SEQUENCE public.signal_hit_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.signal_hit_id_seq OWNER TO root;

--
-- Name: signal_hit_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: root
--

ALTER SEQUENCE public.signal_hit_id_seq OWNED BY public.signal_hit.id;


--
-- Name: signal_strength; Type: TABLE; Schema: public; Owner: root
--

CREATE TABLE public.signal_strength (
    id integer NOT NULL,
    code character varying,
    signal character varying,
    value_all double precision,
    value_recent double precision
);


ALTER TABLE public.signal_strength OWNER TO root;

--
-- Name: signal_strength_id_seq; Type: SEQUENCE; Schema: public; Owner: root
--

CREATE SEQUENCE public.signal_strength_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.signal_strength_id_seq OWNER TO root;

--
-- Name: signal_strength_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: root
--

ALTER SEQUENCE public.signal_strength_id_seq OWNED BY public.signal_strength.id;


--
-- Name: stock; Type: TABLE; Schema: public; Owner: root
--

CREATE TABLE public.stock (
    id integer NOT NULL,
    date date,
    ask double precision,
    bid double precision,
    open double precision,
    high double precision,
    low double precision,
    close double precision,
    volume double precision,
    turnover double precision,
    code character varying
);


ALTER TABLE public.stock OWNER TO root;

--
-- Name: stock_id_seq; Type: SEQUENCE; Schema: public; Owner: root
--

CREATE SEQUENCE public.stock_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.stock_id_seq OWNER TO root;

--
-- Name: stock_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: root
--

ALTER SEQUENCE public.stock_id_seq OWNED BY public.stock.id;


--
-- Name: stock_price; Type: TABLE; Schema: public; Owner: root
--

CREATE TABLE public.stock_price (
    id integer NOT NULL,
    date date,
    open double precision,
    high double precision,
    low double precision,
    close double precision,
    volume double precision,
    adj double precision,
    code character varying
);


ALTER TABLE public.stock_price OWNER TO root;

--
-- Name: stock_price_id_seq; Type: SEQUENCE; Schema: public; Owner: root
--

CREATE SEQUENCE public.stock_price_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.stock_price_id_seq OWNER TO root;

--
-- Name: stock_price_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: root
--

ALTER SEQUENCE public.stock_price_id_seq OWNED BY public.stock_price.id;


--
-- Name: test; Type: TABLE; Schema: public; Owner: root
--

CREATE TABLE public.test (
    id integer,
    date date,
    ask double precision,
    bid double precision,
    open double precision,
    high double precision,
    low double precision,
    close double precision,
    volume double precision,
    turnover double precision,
    code character varying
);


ALTER TABLE public.test OWNER TO root;

--
-- Name: ccass id; Type: DEFAULT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.ccass ALTER COLUMN id SET DEFAULT nextval('public.ccass_id_seq'::regclass);


--
-- Name: option id; Type: DEFAULT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.option ALTER COLUMN id SET DEFAULT nextval('public.option_id_seq'::regclass);


--
-- Name: signal_hit id; Type: DEFAULT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.signal_hit ALTER COLUMN id SET DEFAULT nextval('public.signal_hit_id_seq'::regclass);


--
-- Name: signal_strength id; Type: DEFAULT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.signal_strength ALTER COLUMN id SET DEFAULT nextval('public.signal_strength_id_seq'::regclass);


--
-- Name: stock id; Type: DEFAULT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.stock ALTER COLUMN id SET DEFAULT nextval('public.stock_id_seq'::regclass);


--
-- Name: stock_price id; Type: DEFAULT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.stock_price ALTER COLUMN id SET DEFAULT nextval('public.stock_price_id_seq'::regclass);


--
-- Name: ccass ccass_pkey; Type: CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.ccass
    ADD CONSTRAINT ccass_pkey PRIMARY KEY (id);


--
-- Name: option option_pkey; Type: CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.option
    ADD CONSTRAINT option_pkey PRIMARY KEY (id);


--
-- Name: signal_hit signal_hit_pkey; Type: CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.signal_hit
    ADD CONSTRAINT signal_hit_pkey PRIMARY KEY (id);


--
-- Name: signal_strength signal_strength_pkey; Type: CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.signal_strength
    ADD CONSTRAINT signal_strength_pkey PRIMARY KEY (id);


--
-- Name: stock stock_pkey; Type: CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.stock
    ADD CONSTRAINT stock_pkey PRIMARY KEY (id);


--
-- Name: stock_price stock_price_pkey; Type: CONSTRAINT; Schema: public; Owner: root
--

ALTER TABLE ONLY public.stock_price
    ADD CONSTRAINT stock_price_pkey PRIMARY KEY (id);


--
-- Name: ccass_code_idx; Type: INDEX; Schema: public; Owner: root
--

CREATE INDEX ccass_code_idx ON public.ccass USING btree (code);


--
-- Name: ccass_participant_code_idx; Type: INDEX; Schema: public; Owner: root
--

CREATE INDEX ccass_participant_code_idx ON public.ccass USING btree (participant_code);


--
-- Name: option_code_idx; Type: INDEX; Schema: public; Owner: root
--

CREATE INDEX option_code_idx ON public.option USING btree (code);


--
-- Name: option_date_idx; Type: INDEX; Schema: public; Owner: root
--

CREATE INDEX option_date_idx ON public.option USING btree (date);


--
-- Name: signal_hit_code_idx; Type: INDEX; Schema: public; Owner: root
--

CREATE INDEX signal_hit_code_idx ON public.signal_hit USING btree (code);


--
-- Name: signal_hit_date_idx; Type: INDEX; Schema: public; Owner: root
--

CREATE INDEX signal_hit_date_idx ON public.signal_hit USING btree (date);


--
-- Name: signal_strength_code_idx; Type: INDEX; Schema: public; Owner: root
--

CREATE INDEX signal_strength_code_idx ON public.signal_strength USING btree (code);


--
-- Name: stock_code_idx; Type: INDEX; Schema: public; Owner: root
--

CREATE INDEX stock_code_idx ON public.stock USING btree (code);


--
-- Name: stock_date_idx; Type: INDEX; Schema: public; Owner: root
--

CREATE INDEX stock_date_idx ON public.stock USING btree (date);


--
-- Name: stock_price_code_idx; Type: INDEX; Schema: public; Owner: root
--

CREATE INDEX stock_price_code_idx ON public.stock_price USING btree (code);


--
-- Name: stock_price_date_idx; Type: INDEX; Schema: public; Owner: root
--

CREATE INDEX stock_price_date_idx ON public.stock_price USING btree (date);


--
-- PostgreSQL database dump complete
--

