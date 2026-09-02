-- Schema agro_estudo, com todas as chaves primárias padronizadas como "id"
-- (assim funciona certinho com os endpoints /{table}/{id} da API,
-- que esperam uma coluna chamada "id" em cada tabela)

CREATE TABLE fazendas (
    id              SERIAL PRIMARY KEY,
    nome            VARCHAR(100) NOT NULL,
    cidade          VARCHAR(80) NOT NULL,
    area_hectares   NUMERIC(10,2)
);

CREATE TABLE funcionarios (
    id              SERIAL PRIMARY KEY,
    nome            VARCHAR(100) NOT NULL,
    cargo           VARCHAR(60) NOT NULL,
    id_fazenda      INTEGER NOT NULL REFERENCES fazendas(id),
    ativo           BOOLEAN DEFAULT TRUE
);

CREATE TABLE maquinas (
    id              SERIAL PRIMARY KEY,
    patrimonio      VARCHAR(20) NOT NULL UNIQUE,
    descricao       VARCHAR(100) NOT NULL,
    tipo            VARCHAR(50) NOT NULL,
    id_fazenda      INTEGER NOT NULL REFERENCES fazendas(id),
    ativo           BOOLEAN DEFAULT TRUE
);

CREATE TABLE operacoes (
    id              SERIAL PRIMARY KEY,
    descricao       VARCHAR(100) NOT NULL
);

CREATE TABLE ordens_servico (
    id                  SERIAL PRIMARY KEY,
    id_fazenda          INTEGER NOT NULL REFERENCES fazendas(id),
    id_operacao         INTEGER NOT NULL REFERENCES operacoes(id),
    data_abertura       DATE NOT NULL,
    data_fechamento     DATE,
    status              VARCHAR(30) NOT NULL CHECK (status IN ('ABERTA','EM ANDAMENTO','CONCLUIDA'))
);

CREATE TABLE abastecimentos (
    id                  SERIAL PRIMARY KEY,
    id_funcionario      INTEGER NOT NULL REFERENCES funcionarios(id),
    id_maquina          INTEGER NOT NULL REFERENCES maquinas(id),
    data_abastecimento  TIMESTAMP NOT NULL,
    litros              NUMERIC(10,2) NOT NULL CHECK (litros > 0),
    horimetro           NUMERIC(10,1)
);

INSERT INTO fazendas (nome,cidade,area_hectares) VALUES
('Fazenda Horizonte','Ourinhos - SP',1250),
('Fazenda Primavera','Santa Cruz do Rio Pardo - SP',980),
('Fazenda Beira Mar','Porto Alegre - RS',980),
('Fazenda Boa Vista','Duartina - SP',980),
('Fazenda Esperanca','Espirito Santo do Turvo - SP',1430);

INSERT INTO funcionarios (nome,cargo,id_fazenda) VALUES
('Carlos Silva','Operador Agricola',1),
('Marina Costa','Operadora Agricola',1),
('Rafael Souza','Operador Agricola',4),
('Ana Martins','Assistente Administrativo',2),
('Romeu Rocha','Departamento Pessoal',1),
('Bruno Lima','Operador Agricola',3),
('Juliana Rocha','Almoxarife',5);

INSERT INTO maquinas (patrimonio,descricao,tipo,id_fazenda) VALUES
('MAQ-001','John Deere 6110J','TRATOR',1),
('MAQ-002','Massey Ferguson MF 6713R','TRATOR',1),
('MAQ-003','Jacto Uniport 3030','PULVERIZADOR',2),
('MAQ-004','Valtra A134','TRATOR',2),
('MAQ-005','John Deere S770','COLHEDORA',3),
('MAQ-006','New Holland T7.190','TRATOR',3);

INSERT INTO operacoes (descricao) VALUES
('Preparo de Solo'),('Plantio'),('Aplicacao de Insumos'),('Colheita'),('Transporte Interno');

INSERT INTO ordens_servico (id_fazenda,id_operacao,data_abertura,data_fechamento,status) VALUES
(1,2,'2026-08-01','2026-08-03','CONCLUIDA'),
(2,1,'2026-08-04',NULL,'EM ANDAMENTO'),
(1,3,'2026-08-05',NULL,'ABERTA'),
(3,4,'2026-08-06','2026-08-09','CONCLUIDA'),
(2,5,'2026-08-08',NULL,'EM ANDAMENTO'),
(3,3,'2026-08-10',NULL,'ABERTA');

INSERT INTO abastecimentos (id_funcionario,id_maquina,data_abastecimento,litros,horimetro) VALUES
(1,1,'2026-08-01 08:15',72.5,1205.4),
(2,2,'2026-08-01 14:30',58,894.2),
(3,3,'2026-08-02 09:10',96,2301.8),
(3,4,'2026-08-03 16:20',81.5,1780.6),
(6,5,'2026-08-04 07:45',135,3105.1),
(1,1,'2026-08-05 15:05',64,1218.7),
(2,2,'2026-08-06 10:40',76.5,910.5),
(6,6,'2026-08-07 13:25',88,1567.9),
(3,4,'2026-08-08 17:10',69,1798.2),
(1,2,'2026-08-09 11:35',51.5,925.8);
