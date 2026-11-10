"""Use PyMySQL as the MySQL driver (no compiler toolchain required)."""
import pymysql

pymysql.install_as_MySQLdb()
