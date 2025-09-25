import os
import json
import tempfile
import shutil
import unittest
from unittest.mock import MagicMock

from sariftoolkit.plugins.splitter import Splitter
from sariftoolkit.sarif.models import (
    SarifModel, RunsModel, ToolModel, DriverModel, RulesModel, 
    ResultsModel, MessageModel, LocationsModel, PhysicallocationModel,
    ArtifactlocationModel, PropertiesModel, AutomationDetailsModel
)


class TestSplitter(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.test_dir = tempfile.mkdtemp()
        self.splitter = Splitter()
        
        # Mock logger to avoid log output during tests
        self.splitter.logger = MagicMock()
        
    def tearDown(self):
        """Clean up after each test method."""
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def _create_test_sarif(self, results_data):
        """Create a test SARIF model with specified results data."""
        # Create rules with different security severities
        rules = []
        for i, (rule_id, security_severity) in enumerate([
            ("critical-rule", "9.5"),
            ("high-rule", "7.8"), 
            ("medium-rule", "5.2"),
            ("low-rule", "2.1")
        ]):
            # Create properties with security_severity manually
            props = PropertiesModel()
            props.security_severity = security_severity
            
            rule = RulesModel(
                id=rule_id,
                properties=props
            )
            rules.append(rule)
        
        # Create tool and driver
        driver = DriverModel(
            name="TestTool",
            semanticVersion="1.0.0",
            rules=rules
        )
        tool = ToolModel(driver=driver)
        
        # Create results
        results = []
        for rule_id, file_path in results_data:
            result = ResultsModel(
                ruleId=rule_id,
                message=MessageModel(text=f"Test message for {rule_id}"),
                locations=[LocationsModel(
                    physicalLocation=PhysicallocationModel(
                        artifactLocation=ArtifactlocationModel(uri=file_path)
                    )
                )]
            )
            results.append(result)
        
        # Create run and SARIF
        run = RunsModel(tool=tool, results=results)
        sarif = SarifModel(runs=[run], version="2.1.0")
        
        return sarif
    
    def test_severity_splitting_creates_correct_categories(self):
        """Test that severity-based splitting creates the expected categories."""
        # Create test SARIF with results for each severity level
        results_data = [
            ("critical-rule", "src/critical.py"),
            ("critical-rule", "src/critical2.py"), 
            ("high-rule", "src/high.py"),
            ("high-rule", "src/high2.py"),
            ("high-rule", "src/high3.py"),
            ("medium-rule", "src/medium.py"),
            ("low-rule", "src/low.py")
        ]
        
        sarif = self._create_test_sarif(results_data)
        
        # Create arguments mock
        args = MagicMock()
        args.output = self.test_dir
        
        # Set up splitter for severity splitting
        self.splitter.split_by_severity = True
        self.splitter.language = "python"
        self.splitter._set_default_severity_rules()
        
        # Run severity splitting
        split_results = self.splitter._split_by_severity_levels(sarif, "test.sarif", args)
        
        # Verify the correct number of categories were created
        self.assertEqual(len(split_results), 4)  # Critical, High, Medium, Low
        
        # Verify each category has the correct number of alerts
        category_counts = {result['category'].split('/')[-1]: result['alerts'] for result in split_results}
        
        self.assertEqual(category_counts.get('severity:Critical', 0), 2)
        self.assertEqual(category_counts.get('severity:High', 0), 3) 
        self.assertEqual(category_counts.get('severity:Medium', 0), 1)
        self.assertEqual(category_counts.get('severity:Low', 0), 1)
        
        # Verify automation details are set correctly
        for result in split_results:
            self.assertTrue(result['category'].startswith('/language:python/severity:'))
    
    def test_path_splitting_creates_correct_categories(self):
        """Test that path-based splitting creates the expected categories."""
        # Create test SARIF with results for different path patterns
        results_data = [
            ("test-rule", "tests/unit/test_file.py"),
            ("test-rule", "test/integration/test_api.py"),
            ("app-rule", "src/main.py"),
            ("app-rule", "api/handler.py"),
            ("other-rule", "config/settings.py")
        ]
        
        sarif = self._create_test_sarif(results_data)
        
        # Create arguments mock
        args = MagicMock()
        args.output = self.test_dir
        
        # Set up splitter for path splitting
        self.splitter.split_by_path = True
        self.splitter.language = "python"
        self.splitter._set_default_path_rules()
        
        # Run path splitting
        split_results = self.splitter._split_by_path_patterns(sarif, "test.sarif", args)
        
        # Verify categories were created
        self.assertGreater(len(split_results), 0)
        
        # Check that test files are categorized correctly
        test_category_found = any('category:Tests' in result['category'] for result in split_results)
        app_category_found = any('category:App' in result['category'] for result in split_results)
        
        self.assertTrue(test_category_found or app_category_found)
    
    def test_single_splitting_method_restriction(self):
        """Test that only one splitting method can be enabled at a time."""
        # Create test arguments
        args = MagicMock()
        args.sarif = "test.sarif"
        args.output = self.test_dir
        args.path_config = None
        args.severity_config = None
        
        # Set both splitting methods to True
        self.splitter.split_by_path = True
        self.splitter.split_by_severity = True
        
        # Mock loadSarif to avoid file loading
        self.splitter.loadSarif = MagicMock(return_value=[])
        
        # Run should exit early with error log
        self.splitter.run(args)
        
        # Verify error was logged
        self.splitter.logger.error.assert_called_with(
            "Only one splitting method can be enabled at a time. Choose either --split-by-path or --split-by-severity"
        )
    
    def test_no_alerts_are_dropped(self):
        """Test that all alerts are preserved during splitting."""
        # Create test SARIF with mixed results
        results_data = [
            ("critical-rule", "src/critical.py"),
            ("high-rule", "src/high.py"), 
            ("unknown-rule", "src/unknown.py")  # This will not match any severity mapping
        ]
        
        sarif = self._create_test_sarif(results_data)
        
        # Add an additional result with no rule mapping
        unknown_result = ResultsModel(
            ruleId="unmapped-rule",
            message=MessageModel(text="Test message for unmapped rule"),
            locations=[LocationsModel(
                physicalLocation=PhysicallocationModel(
                    artifactLocation=ArtifactlocationModel(uri="src/unmapped.py")
                )
            )]
        )
        sarif.runs[0].results.append(unknown_result)
        
        # Create arguments mock
        args = MagicMock()
        args.output = self.test_dir
        
        # Set up splitter for severity splitting
        self.splitter.split_by_severity = True
        self.splitter.language = "python"
        self.splitter._set_default_severity_rules()
        
        # Count original alerts
        original_count = len(sarif.runs[0].results)
        
        # Run severity splitting
        split_results = self.splitter._split_by_severity_levels(sarif, "test.sarif", args)
        
        # Count total split alerts
        total_split_alerts = sum(result['alerts'] for result in split_results)
        
        # Verify no alerts were dropped
        self.assertEqual(original_count, total_split_alerts)
    
    def test_automation_details_are_set_correctly(self):
        """Test that runAutomationDetails are set correctly in output files."""
        # Create simple test SARIF
        results_data = [("high-rule", "src/test.py")]
        sarif = self._create_test_sarif(results_data)
        
        # Create arguments mock
        args = MagicMock()
        args.output = self.test_dir
        
        # Set up splitter
        self.splitter.split_by_severity = True
        self.splitter.language = "java"  # Use different language to test
        self.splitter._set_default_severity_rules()
        
        # Run splitting
        split_results = self.splitter._split_by_severity_levels(sarif, "test.sarif", args)
        
        # Verify automation details format
        self.assertEqual(len(split_results), 1)
        expected_category = "/language:java/severity:High"
        self.assertEqual(split_results[0]['category'], expected_category)
    
    def test_summary_table_output(self):
        """Test that summary table contains correct information."""
        # Create test data
        summary_data = [{
            'original_file': '/path/to/test.sarif',
            'original_alerts': 5,
            'split_results': [
                {'file': 'test-critical.sarif', 'alerts': 2, 'category': '/language:python/severity:Critical'},
                {'file': 'test-high.sarif', 'alerts': 3, 'category': '/language:python/severity:High'}
            ]
        }]
        
        # Capture print output
        import io
        import sys
        captured_output = io.StringIO()
        sys.stdout = captured_output
        
        try:
            self.splitter._print_summary_table(summary_data)
            output = captured_output.getvalue()
            
            # Verify summary table content
            self.assertIn("SARIF SPLITTING SUMMARY", output)
            self.assertIn("test.sarif", output)
            self.assertIn("5", output)  # Original alerts count
            self.assertIn("test-critical.sarif", output)
            self.assertIn("test-high.sarif", output)
            self.assertIn("/language:python/severity:Critical", output)
            self.assertIn("/language:python/severity:High", output)
            self.assertIn("TOTALS:", output)
            
        finally:
            sys.stdout = sys.__stdout__


if __name__ == '__main__':
    unittest.main()