from uuid import uuid4

from app.database.postgres import PostgresDB, as_uuid, translate_constraint_errors


def _user(row):
    if row is None:
        return None
    return {**dict(row), "id": str(row["id"])}


class PostgresUserRepository:
    @translate_constraint_errors
    async def create(self, data):
        user_id = uuid4()
        async with PostgresDB.get_pool().acquire() as connection:
            row = await connection.fetchrow(
                "INSERT INTO users (id, full_name, email, phone, password_hash, role, created_at) "
                "VALUES ($1,$2,$3,$4,$5,$6,$7) "
                "RETURNING id, full_name, email, phone, password_hash, role, created_at",
                user_id, data["full_name"], data["email"], data.get("phone"),
                data["password_hash"], data["role"], data["created_at"],
            )
        return _user(row)

    async def find_by_id(self, user_id):
        async with PostgresDB.get_pool().acquire() as connection:
            return _user(await connection.fetchrow(
                "SELECT id, full_name, email, phone, password_hash, role, created_at FROM users WHERE id=$1", as_uuid(user_id)
            ))

    async def find_by_email(self, email):
        async with PostgresDB.get_pool().acquire() as connection:
            return _user(await connection.fetchrow(
                "SELECT id, full_name, email, phone, password_hash, role, created_at FROM users WHERE email=$1", email
            ))

    async def find_all(self):
        async with PostgresDB.get_pool().acquire() as connection:
            rows = await connection.fetch("SELECT id, full_name, email, phone, password_hash, role, created_at FROM users ORDER BY created_at DESC")
        return [_user(row) for row in rows]

    @translate_constraint_errors
    async def update(self, user_id, data):
        if not data:
            return await self.find_by_id(user_id)
        allowed = {"full_name", "email", "phone", "password_hash", "role"}
        if not set(data) <= allowed:
            raise ValueError("Unsupported user fields")
        assignments = ", ".join(f"{field}=${index}" for index, field in enumerate(data, start=2))
        values = [as_uuid(user_id), *data.values()]
        async with PostgresDB.get_pool().acquire() as connection:
            row = await connection.fetchrow(
                f"UPDATE users SET {assignments} WHERE id=$1 RETURNING id, full_name, email, phone, password_hash, role, created_at", *values
            )
        return _user(row)

    @translate_constraint_errors
    async def delete(self, user_id):
        async with PostgresDB.get_pool().acquire() as connection:
            status = await connection.execute("DELETE FROM users WHERE id=$1", as_uuid(user_id))
        return status.endswith("1")
