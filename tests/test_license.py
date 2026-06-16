import importlib


def test_license_generation_and_validation_roundtrip(temp_env):
    license_mod = importlib.import_module("manager.license")

    key = license_mod.generate_key("buyer@example.com", 10)
    result = license_mod.validate_key(key, "buyer@example.com")

    assert result["is_valid"] is True
    assert result["max_users"] == 10
    assert result["customer_email"] == "buyer@example.com"
