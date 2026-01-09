"""
Temel smoke test - CI/CD için minimal test
Bu test temel import ve konfigürasyon işlemlerini kontrol eder.
"""

import unittest
import sys
import os


class TestBasicFunctionality(unittest.TestCase):
    """Temel fonksiyonalite testleri"""

    def test_basic_imports(self):
        """Temel import işlemleri testi"""
        # Test Python version
        self.assertGreaterEqual(sys.version_info.major, 3)
        self.assertGreaterEqual(sys.version_info.minor, 8)

        # Test basic modules
        import json
        import datetime
        import os

        self.assertTrue(True)  # Basic import success

    def test_project_structure(self):
        """Proje yapısı testi"""
        # Get project root
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(
            current_dir
        )  # tests klasörünün üstü proje root'u

        # Check essential files
        essential_files = [
            "pyproject.toml",
            "requirements.txt",
            "requirements-dev.txt",
            "README.md",
        ]

        for file_name in essential_files:
            file_path = os.path.join(project_root, file_name)
            self.assertTrue(
                os.path.exists(file_path), f"Missing essential file: {file_name}"
            )

    def test_src_directory_structure(self):
        """Src dizin yapısı testi"""
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(
            current_dir
        )  # tests klasörünün üstü proje root'u
        src_dir = os.path.join(project_root, "src")

        # Check src directory exists
        self.assertTrue(os.path.exists(src_dir), "src directory missing")

        # Check essential subdirectories
        essential_dirs = ["services", "utils", "config", "core", "models"]

        for dir_name in essential_dirs:
            dir_path = os.path.join(src_dir, dir_name)
            self.assertTrue(
                os.path.exists(dir_path), f"Missing src subdirectory: {dir_name}"
            )

    def test_requirements_file_content(self):
        """Requirements dosyası içerik testi"""
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(
            current_dir
        )  # tests klasörünün üstü proje root'u
        req_file = os.path.join(project_root, "requirements.txt")

        if os.path.exists(req_file):
            with open(req_file, "r") as f:
                content = f.read()

            # Check for essential packages
            essential_packages = ["python-binance", "PySide6", "pandas", "requests"]

            for package in essential_packages:
                self.assertIn(package, content, f"Missing essential package: {package}")

    def test_configuration_files(self):
        """Konfigürasyon dosyaları testi"""
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(
            current_dir
        )  # tests klasörünün üstü proje root'u
        config_dir = os.path.join(project_root, "config")

        if os.path.exists(config_dir):
            # Check for example files
            example_files = ["preferences.example.txt", "fav_coins_example.json"]

            for file_name in example_files:
                file_path = os.path.join(config_dir, file_name)
                # It's OK if example files don't exist, but check if directory is readable
                self.assertTrue(
                    os.access(config_dir, os.R_OK), f"Config directory not readable"
                )

    def test_data_directory_structure(self):
        """Data dizin yapısı testi"""
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(
            current_dir
        )  # tests klasörünün üstü proje root'u
        data_dir = os.path.join(project_root, "data")

        if os.path.exists(data_dir):
            # Check for essential subdirectories
            data_subdirs = ["trades", "portfolio", "analytics"]

            for subdir_name in data_subdirs:
                subdir_path = os.path.join(data_dir, subdir_name)
                if os.path.exists(subdir_path):
                    self.assertTrue(
                        os.path.isdir(subdir_path),
                        f"Data subdirectory is not a directory: {subdir_name}",
                    )

    def test_basic_math_operations(self):
        """Temel matematik işlemleri testi"""
        # Test basic calculations that would be used in trading
        price = 50000.0
        quantity = 0.001
        total = price * quantity

        self.assertEqual(total, 50.0)

        # Test percentage calculations
        percentage = 0.05  # 5%
        risk_amount = 1000.0 * percentage

        self.assertEqual(risk_amount, 50.0)

        # Test precision handling
        result = round(0.123456789, 6)
        self.assertEqual(result, 0.123457)

    def test_datetime_operations(self):
        """Datetime işlemleri testi"""
        import datetime

        # Test current time
        now = datetime.datetime.now()
        self.assertIsInstance(now, datetime.datetime)

        # Test ISO format
        iso_time = now.isoformat()
        self.assertIsInstance(iso_time, str)
        self.assertIn("T", iso_time)  # ISO format should contain 'T'

        # Test date formatting
        date_str = now.strftime("%Y-%m-%d")
        self.assertEqual(len(date_str), 10)  # YYYY-MM-DD format

    def test_json_operations(self):
        """JSON işlemleri testi"""
        import json

        # Test JSON serialization
        test_data = {
            "symbol": "BTCUSDT",
            "price": 50000.0,
            "quantity": 0.001,
            "timestamp": "2025-09-12T10:00:00",
        }

        # Serialize to JSON
        json_str = json.dumps(test_data)
        self.assertIsInstance(json_str, str)

        # Deserialize from JSON
        parsed_data = json.loads(json_str)
        self.assertEqual(parsed_data, test_data)

        # Test JSON with lists
        list_data = [
            {"name": "BTC", "symbol": "BTCUSDT"},
            {"name": "ETH", "symbol": "ETHUSDT"},
        ]

        json_list_str = json.dumps(list_data)
        parsed_list = json.loads(json_list_str)
        self.assertEqual(len(parsed_list), 2)

    def test_file_operations(self):
        """Dosya işlemleri testi"""
        import tempfile

        # Test temporary file operations
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as temp_file:
            temp_file.write("test content")
            temp_file_path = temp_file.name

        # Read the file back
        with open(temp_file_path, "r") as f:
            content = f.read()

        self.assertEqual(content, "test content")

        # Clean up
        os.unlink(temp_file_path)


if __name__ == "__main__":
    unittest.main()
