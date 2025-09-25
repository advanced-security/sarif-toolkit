import os
import copy
import fnmatch
from typing import List, Dict, Any
from dataclasses import dataclass, field
from argparse import ArgumentParser

from sariftoolkit.plugin import Plugin
from sariftoolkit.sarif.sarif import exportSarif
from sariftoolkit.sarif.models import SarifModel, RunsModel


@dataclass
class PathSplitRule:
    name: str
    patterns: List[str]


@dataclass
class SeveritySplitRule:
    name: str
    severities: List[str]  # e.g., ["critical"], ["high", "medium"], ["*"]


@dataclass
class Splitter(Plugin):
    name: str = "Splitter"
    version: str = "1.0.0"
    description: str = "SARIF File Splitter by Categories"
    
    split_by_path: bool = False
    split_by_severity: bool = False
    path_rules: List[PathSplitRule] = field(default_factory=list)
    severity_rules: List[SeveritySplitRule] = field(default_factory=list)
    language: str = "unknown"
    
    def arguments(self, parser: ArgumentParser):
        parser.add_argument(
            "--split-by-path", 
            action="store_true", 
            help="Split SARIF by file path patterns"
        )
        parser.add_argument(
            "--split-by-severity", 
            action="store_true", 
            help="Split SARIF by security severity levels"
        )
        parser.add_argument(
            "--language", 
            default="unknown", 
            help="Programming language for category naming (default: unknown)"
        )
        parser.add_argument(
            "--path-config", 
            help="JSON configuration file for path-based splitting rules"
        )
        parser.add_argument(
            "--severity-config", 
            help="JSON configuration file for severity-based splitting rules"
        )
    
    def run(self, arguments, **kwargs):
        if not arguments.sarif:
            self.logger.error("SARIF file path is required")
            return
        
        self.split_by_path = arguments.split_by_path
        self.split_by_severity = arguments.split_by_severity
        self.language = arguments.language
        
        if not self.split_by_path and not self.split_by_severity:
            self.logger.error("At least one splitting method must be enabled (--split-by-path or --split-by-severity)")
            return
        
        # Load configuration
        if arguments.path_config:
            self._load_path_config(arguments.path_config)
        else:
            self._set_default_path_rules()
            
        if arguments.severity_config:
            self._load_severity_config(arguments.severity_config)
        else:
            self._set_default_severity_rules()
        
        # Load SARIF files
        sarif_files = self.loadSarif(arguments.sarif)
        
        for sarif_model, sarif_file_path in sarif_files:
            self.logger.info(f"Processing SARIF file: {sarif_file_path}")
            
            if self.split_by_path:
                self._split_by_path_patterns(sarif_model, sarif_file_path, arguments)
            
            if self.split_by_severity:
                self._split_by_severity_levels(sarif_model, sarif_file_path, arguments)
    
    def _set_default_path_rules(self):
        """Set default path-based splitting rules"""
        self.path_rules = [
            PathSplitRule(name="Tests", patterns=["**/test/**", "**/tests/**", "**/*test*"]),
            PathSplitRule(name="App", patterns=["**/web/**", "**/api/**", "**/src/**", "**/app/**"])
        ]
    
    def _set_default_severity_rules(self):
        """Set default severity-based splitting rules"""
        self.severity_rules = [
            SeveritySplitRule(name="Critical", severities=["critical"]),
            SeveritySplitRule(name="High-Medium", severities=["high", "medium"]),
            SeveritySplitRule(name="Others", severities=["*"])  # Catch-all for remaining
        ]
    
    def _load_path_config(self, config_path: str):
        """Load path configuration from JSON file"""
        import json
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
                self.path_rules = [
                    PathSplitRule(name=rule['name'], patterns=rule['patterns'])
                    for rule in config.get('path_rules', [])
                ]
        except Exception as e:
            self.logger.error(f"Failed to load path config: {e}")
            self._set_default_path_rules()
    
    def _load_severity_config(self, config_path: str):
        """Load severity configuration from JSON file"""
        import json
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
                self.severity_rules = [
                    SeveritySplitRule(name=rule['name'], severities=rule['severities'])
                    for rule in config.get('severity_rules', [])
                ]
        except Exception as e:
            self.logger.error(f"Failed to load severity config: {e}")
            self._set_default_severity_rules()
    
    def _split_by_path_patterns(self, sarif: SarifModel, sarif_file_path: str, arguments):
        """Split SARIF file by file path patterns"""
        self.logger.info("Splitting by path patterns")
        
        # Create category buckets
        path_buckets = {}
        unmatched_results = []
        
        for run in sarif.runs:
            tool = run.tool.driver
            self.logger.info(f"Processing tool: {tool.name} ({tool.semanticVersion})")
            
            # Initialize buckets for this run  
            for rule in self.path_rules:
                category_name = f"/language:{self.language}/category:{rule.name}"
                if category_name not in path_buckets:
                    path_buckets[category_name] = {
                        'run': copy.deepcopy(run),
                        'results': []
                    }
                    path_buckets[category_name]['run'].results = []
            
            # Process each result
            for result in run.results:
                matched = False
                
                # Get the primary location URI
                if result.locations and len(result.locations) > 0:
                    location = result.locations[0]
                    if location.physicalLocation and location.physicalLocation.artifactLocation:
                        uri = location.physicalLocation.artifactLocation.uri
                        self.logger.debug(f"Checking URI: {uri} for result {result.ruleId}")
                        
                        # Check against path rules
                        for rule in self.path_rules:
                            for pattern in rule.patterns:
                                if fnmatch.fnmatch(uri, pattern):
                                    category_name = f"/language:{self.language}/category:{rule.name}"
                                    path_buckets[category_name]['results'].append(result)
                                    matched = True
                                    self.logger.debug(f"Matched {uri} to category {rule.name}")
                                    break
                            if matched:
                                break
                
                if not matched:
                    unmatched_results.append(result)
        
        # Handle unmatched results with fallback category
        if unmatched_results:
            fallback_category = f"/language:{self.language}/filter:none"
            path_buckets[fallback_category] = {
                'run': copy.deepcopy(sarif.runs[0]),
                'results': unmatched_results
            }
            path_buckets[fallback_category]['run'].results = []
        
        # Create and export split SARIF files
        self._export_split_files(path_buckets, sarif, sarif_file_path, "path", arguments)
    
    def _split_by_severity_levels(self, sarif: SarifModel, sarif_file_path: str, arguments):
        """Split SARIF file by security severity levels"""
        self.logger.info("Splitting by severity levels")
        
        # Build rule severity map
        rule_severity_map = {}
        for run in sarif.runs:
            for rule in run.tool.driver.rules:
                if rule.properties:
                    # Try different ways to access security-severity property
                    security_severity = None
                    
                    # Check if it's a dictionary-like object
                    if hasattr(rule.properties, '__dict__'):
                        props = rule.properties.__dict__
                        # Try common variations of the property name
                        security_severity = (props.get('security-severity') or 
                                           props.get('security_severity') or
                                           props.get('securitySeverity'))
                    
                    # If it's a dataclass with direct attribute access
                    if not security_severity:
                        for attr_name in ['security-severity', 'security_severity', 'securitySeverity']:
                            try:
                                security_severity = getattr(rule.properties, attr_name, None)
                                if security_severity:
                                    break
                            except:
                                pass
                    
                    if security_severity:
                        try:
                            # Convert security-severity to severity category
                            severity_val = float(security_severity)
                            if severity_val >= 9.0:
                                severity = "critical"
                            elif severity_val >= 7.0:
                                severity = "high"
                            elif severity_val >= 4.0:
                                severity = "medium"
                            else:
                                severity = "low"
                            rule_severity_map[rule.id] = severity
                            self.logger.debug(f"Rule {rule.id} has security-severity {security_severity} -> {severity}")
                        except ValueError:
                            self.logger.warning(f"Invalid security-severity value for rule {rule.id}: {security_severity}")
                    else:
                        self.logger.debug(f"No security-severity found for rule {rule.id}")
        
        # Create severity buckets
        severity_buckets = {}
        unmatched_results = []
        
        for run in sarif.runs:
            tool = run.tool.driver
            self.logger.info(f"Processing tool: {tool.name} ({tool.semanticVersion})")
            
            # Initialize severity buckets for this run
            for rule in self.severity_rules:
                if rule.severities != ["*"]:  # Skip catch-all initially
                    category_name = f"/language:{self.language}/severity:{rule.name}"
                    if category_name not in severity_buckets:
                        severity_buckets[category_name] = {
                            'run': copy.deepcopy(run),
                            'results': []
                        }
                        severity_buckets[category_name]['run'].results = []
            
            # Process each result
            for result in run.results:
                matched = False
                result_severity = rule_severity_map.get(result.ruleId)
                
                if result_severity:
                    # Check against severity rules (excluding catch-all)
                    for rule in self.severity_rules:
                        if rule.severities != ["*"] and result_severity in rule.severities:
                            category_name = f"/language:{self.language}/severity:{rule.name}"
                            severity_buckets[category_name]['results'].append(result)
                            matched = True
                            self.logger.debug(f"Matched {result.ruleId} with severity {result_severity} to {rule.name}")
                            break
                
                if not matched:
                    unmatched_results.append(result)
        
        # Handle unmatched results with catch-all category
        if unmatched_results:
            catch_all_rule = next((rule for rule in self.severity_rules if rule.severities == ["*"]), None)
            if catch_all_rule:
                category_name = f"/language:{self.language}/severity:{catch_all_rule.name}"
                severity_buckets[category_name] = {
                    'run': copy.deepcopy(sarif.runs[0]),
                    'results': unmatched_results
                }
                severity_buckets[category_name]['run'].results = []
        
        # Create and export split SARIF files
        self._export_split_files(severity_buckets, sarif, sarif_file_path, "severity", arguments)
    
    def _export_split_files(self, buckets: Dict[str, Dict], original_sarif: SarifModel, 
                           original_file_path: str, split_type: str, arguments):
        """Export split SARIF files with proper runAutomationDetails"""
        
        base_name, ext = os.path.splitext(original_file_path)
        
        for category, bucket in buckets.items():
            if not bucket['results']:
                self.logger.info(f"Skipping empty category: {category}")
                continue
                
            # Create new SARIF model
            new_sarif = copy.deepcopy(original_sarif)
            new_sarif.runs = [bucket['run']]
            
            # Set results for the run
            new_sarif.runs[0].results = bucket['results']
            
            # Add runAutomationDetails for GitHub Advanced Security
            from sariftoolkit.sarif.models import AutomationDetailsModel
            
            if not new_sarif.runs[0].automationDetails:
                new_sarif.runs[0].automationDetails = AutomationDetailsModel(id=category)
            else:
                new_sarif.runs[0].automationDetails.id = category
            
            # Generate output filename
            safe_category = category.replace("/", "_").replace(":", "-")
            output_file = f"{base_name}-{split_type}-{safe_category}{ext}"
            
            if arguments.output:
                if os.path.isdir(arguments.output):
                    output_file = os.path.join(arguments.output, os.path.basename(output_file))
                else:
                    output_dir = os.path.dirname(arguments.output)
                    if output_dir:
                        output_file = os.path.join(output_dir, os.path.basename(output_file))
                    else:
                        output_file = os.path.join(os.path.dirname(original_file_path), os.path.basename(output_file))
            
            # Export the split SARIF file
            exportSarif(output_file, new_sarif)
            self.logger.info(f"Created split SARIF: {output_file} with {len(bucket['results'])} results for category: {category}")