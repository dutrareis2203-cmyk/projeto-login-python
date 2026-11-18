-- Execute este arquivo no Supabase > SQL Editor > New query > Run.

create table if not exists public.produtos (
    id bigint generated always as identity primary key,
    nome text not null unique,
    preco numeric(10,2) not null check (preco >= 0)
);

create table if not exists public.vendas (
    id bigint generated always as identity primary key,
    pedido_id uuid not null,
    produto_id bigint not null references public.produtos(id),
    quantidade integer not null check (quantidade between 1 and 100),
    preco_unitario numeric(10,2) not null,
    subtotal numeric(10,2) not null,
    criado_em timestamptz not null default now(),
    usuario_id uuid not null default auth.uid()
);

insert into public.produtos (nome, preco) values
('Hambúrguer', 18.00),
('Batata frita', 12.00),
('Refrigerante', 7.00),
('Suco', 9.00),
('Água', 4.00)
on conflict (nome) do update set preco = excluded.preco;

alter table public.produtos enable row level security;
alter table public.vendas enable row level security;

drop policy if exists "Produtos visíveis para usuários autenticados" on public.produtos;
create policy "Produtos visíveis para usuários autenticados"
on public.produtos for select to authenticated using (true);

drop policy if exists "Usuário consulta suas vendas" on public.vendas;
create policy "Usuário consulta suas vendas"
on public.vendas for select to authenticated using (auth.uid() = usuario_id);

drop policy if exists "Usuário registra suas vendas" on public.vendas;
create policy "Usuário registra suas vendas"
on public.vendas for insert to authenticated with check (auth.uid() = usuario_id);
