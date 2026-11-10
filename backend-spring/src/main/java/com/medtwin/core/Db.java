package com.medtwin.core;

import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Component;

import java.util.List;
import java.util.Map;

/** Thin JDBC facade. Models are unmanaged, so every query is explicit SQL over db/schema.sql. */
@Component
public class Db {
    private final JdbcTemplate jdbc;

    public Db(JdbcTemplate jdbc) {
        this.jdbc = jdbc;
    }

    public List<Map<String, Object>> list(String sql, Object... args) {
        return jdbc.queryForList(sql, args);
    }

    public Map<String, Object> one(String sql, Object... args) {
        List<Map<String, Object>> rows = list(sql, args);
        return rows.isEmpty() ? null : rows.get(0);
    }

    public Map<String, Object> require(String sql, Object... args) {
        Map<String, Object> row = one(sql, args);
        if (row == null) throw ApiError.notFound("Not found.");
        return row;
    }

    public int exec(String sql, Object... args) {
        return jdbc.update(sql, (Object[]) args);
    }

    public long count(String sql, Object... args) {
        Long value = jdbc.queryForObject(sql, Long.class, (Object[]) args);
        return value == null ? 0L : value;
    }

    public boolean reachable() {
        try {
            jdbc.queryForObject("SELECT 1", Integer.class);
            return true;
        } catch (Exception exc) {
            return false;
        }
    }
}
