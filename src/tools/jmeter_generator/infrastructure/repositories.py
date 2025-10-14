"""Infrastructure implementation for JMeter generation."""
import xml.etree.ElementTree as ET
from xml.dom import minidom
from urllib.parse import urlparse
from typing import Dict, Any, List
from ..domain.repositories import JMeterRepository
from ..domain.models import (
    JMeterGenerationResult, JMeterTestPlan, JMeterThreadGroup, 
    JMeterHttpRequest, JMeterHeader, JMeterParameter, HttpMethod
)


class XmlJMeterRepository(JMeterRepository):
    """XML implementation of JMeter repository."""
    
    async def generate_jmx_from_swagger(self, swagger_data: Dict[str, Any]) -> JMeterGenerationResult:
        """Generate JMX test plan from swagger analysis result."""
        
        base_urls = swagger_data.get('base_urls', ['http://localhost'])
        base_url = base_urls[0] if base_urls else 'http://localhost'
        
        # Parse base URL
        parsed_url = urlparse(base_url)
        protocol = parsed_url.scheme or 'http'
        host = parsed_url.hostname or 'localhost'
        port = parsed_url.port or (443 if protocol == 'https' else 80)
        
        endpoints = swagger_data.get('endpoints', [])
        
        # Create test plan
        test_plan = JMeterTestPlan(
            name=f"API Test Plan - {swagger_data.get('title', 'Swagger API')}",
            base_url=host,
            port=port,
            protocol=protocol
        )
        
        total_requests = 0
        
        # Create one thread group per endpoint
        for endpoint in endpoints:
            thread_group = self._create_thread_group_from_endpoint(endpoint)
            test_plan.thread_groups.append(thread_group)
            total_requests += len(thread_group.http_requests)
        
        # Generate XML content
        xml_content = self._generate_jmx_xml(test_plan)
        
        return JMeterGenerationResult(
            test_plan=test_plan,
            xml_content=xml_content,
            total_requests=total_requests,
            total_thread_groups=len(test_plan.thread_groups)
        )
    
    async def generate_jmx_from_features(self, features_data: Dict[str, Any]) -> JMeterGenerationResult:
        """Generate JMX test plan from feature files data."""
        
        base_url = features_data.get('base_url', 'http://localhost')
        features = features_data.get('features', [])
        
        # Parse base URL
        parsed_url = urlparse(base_url)
        protocol = parsed_url.scheme or 'http'
        host = parsed_url.hostname or 'localhost'
        port = parsed_url.port or (443 if protocol == 'https' else 80)
        
        # Create test plan
        test_plan = JMeterTestPlan(
            name="API Test Plan - From Features",
            base_url=host,
            port=port,
            protocol=protocol
        )
        
        total_requests = 0
        
        # Create thread groups from features
        for feature in features:
            thread_group = self._create_thread_group_from_feature(feature)
            if thread_group.http_requests:  # Only add if there are requests
                test_plan.thread_groups.append(thread_group)
                total_requests += len(thread_group.http_requests)
        
        # Generate XML content
        xml_content = self._generate_jmx_xml(test_plan)
        
        return JMeterGenerationResult(
            test_plan=test_plan,
            xml_content=xml_content,
            total_requests=total_requests,
            total_thread_groups=len(test_plan.thread_groups)
        )
    
    async def save_jmx_file(self, result: JMeterGenerationResult, file_path: str) -> str:
        """Save JMX file to disk."""
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(result.xml_content)
        return file_path
    
    def _create_thread_group_from_endpoint(self, endpoint: Dict[str, Any]) -> JMeterThreadGroup:
        """Create a thread group from a single endpoint."""
        method = endpoint.get('method', 'GET')
        path = endpoint.get('path', '/')
        summary = endpoint.get('summary', '')
        
        thread_group_name = f"{method} {path}"
        if summary:
            thread_group_name += f" - {summary}"
        
        thread_group = JMeterThreadGroup(name=thread_group_name)
        
        # Create HTTP request
        http_request = self._create_http_request_from_endpoint(endpoint)
        thread_group.http_requests.append(http_request)
        
        return thread_group
    
    def _create_thread_group_from_feature(self, feature: Dict[str, Any]) -> JMeterThreadGroup:
        """Create a thread group from a feature file."""
        feature_name = feature.get('feature_name', 'Feature')
        thread_group = JMeterThreadGroup(name=f"Thread Group - {feature_name}")
        
        scenarios = feature.get('scenarios', [])
        
        for scenario in scenarios:
            # Extract HTTP requests from scenario steps
            http_request = self._extract_http_request_from_scenario(scenario)
            if http_request:
                thread_group.http_requests.append(http_request)
        
        return thread_group
    
    def _create_http_request_from_endpoint(self, endpoint: Dict[str, Any]) -> JMeterHttpRequest:
        """Create an HTTP request from endpoint data."""
        method_str = endpoint.get('method', 'GET').upper()
        method = HttpMethod(method_str)
        path = endpoint.get('path', '/')
        summary = endpoint.get('summary', '')
        
        request_name = f"{method_str} {path}"
        if summary:
            request_name = summary
        
        # Convert headers
        headers = []
        for header_info in endpoint.get('headers', []):
            headers.append(JMeterHeader(
                name=header_info['name'],
                value=self._get_example_value(header_info)
            ))
        
        # Add default headers
        if method in [HttpMethod.POST, HttpMethod.PUT, HttpMethod.PATCH]:
            headers.append(JMeterHeader(name="Content-Type", value="application/json"))
        
        # Convert query parameters
        parameters = []
        for param_info in endpoint.get('query_parameters', []):
            parameters.append(JMeterParameter(
                name=param_info['name'],
                value=self._get_example_value(param_info)
            ))
        
        # Handle request body
        body_data = None
        request_body = endpoint.get('request_body')
        if request_body and method in [HttpMethod.POST, HttpMethod.PUT, HttpMethod.PATCH]:
            body_data = self._generate_request_body_json(request_body)
        
        # Replace path parameters with example values
        final_path = self._replace_path_parameters(path, endpoint.get('path_parameters', []))
        
        return JMeterHttpRequest(
            name=request_name,
            method=method,
            path=final_path,
            headers=headers,
            parameters=parameters,
            body_data=body_data
        )
    
    def _extract_http_request_from_scenario(self, scenario: Dict[str, Any]) -> JMeterHttpRequest:
        """Extract HTTP request information from a scenario."""
        scenario_name = scenario.get('name', 'Request')
        
        # Try to extract method and path from scenario name or steps
        method = HttpMethod.GET
        path = "/"
        
        # Look for method in scenario name
        name_upper = scenario_name.upper()
        for http_method in HttpMethod:
            if http_method.value in name_upper:
                method = http_method
                break
        
        # Try to extract path from scenario name
        if ' /' in scenario_name:
            path_part = scenario_name.split(' /')[1].split(' ')[0]
            path = '/' + path_part
        
        return JMeterHttpRequest(
            name=scenario_name,
            method=method,
            path=path,
            headers=[JMeterHeader(name="Content-Type", value="application/json")],
            parameters=[]
        )
    
    def _get_example_value(self, field: Dict[str, Any]) -> str:
        """Get an example value for a field."""
        if 'example' in field and field['example'] is not None:
            return str(field['example'])
        
        data_type = field.get('data_type', 'string')
        field_format = field.get('format', {})
        
        # Get format value if it's a dict
        if isinstance(field_format, dict):
            format_name = field_format.get('value', 'none')
        else:
            format_name = str(field_format).lower()
        
        # Generate example based on type and format
        if data_type == 'string':
            if 'email' in format_name:
                return 'test@example.com'
            elif 'uuid' in format_name:
                return '123e4567-e89b-12d3-a456-426614174000'
            elif 'date' in format_name:
                return '2023-12-01'
            elif 'phone' in format_name:
                return '+1234567890'
            else:
                return 'example_value'
        elif data_type == 'integer':
            return '123'
        elif data_type == 'number':
            return '123.45'
        elif data_type == 'boolean':
            return 'true'
        else:
            return 'example_value'
    
    def _generate_request_body_json(self, request_body: Dict[str, Any]) -> str:
        """Generate JSON request body from field definitions."""
        if not request_body:
            return '{}'
        
        body_obj = {}
        for field_name, field_info in request_body.items():
            body_obj[field_name] = self._get_example_value(field_info)
        
        import json
        return json.dumps(body_obj, indent=2)
    
    def _replace_path_parameters(self, path: str, path_params: List[Dict[str, Any]]) -> str:
        """Replace path parameters with example values."""
        result_path = path
        for param in path_params:
            param_name = param['name']
            example_value = self._get_example_value(param)
            result_path = result_path.replace(f'{{{param_name}}}', example_value)
        return result_path
    
    def _generate_jmx_xml(self, test_plan: JMeterTestPlan) -> str:
        """Generate JMX XML content from test plan."""
        # Create root element
        root = ET.Element("jmeterTestPlan", version="1.2", properties="5.0", jmeter="5.6.3")
        
        # Add hash tree
        hash_tree = ET.SubElement(root, "hashTree")
        
        # Add test plan element
        test_plan_elem = ET.SubElement(hash_tree, "TestPlan", 
                                     guiclass="TestPlanGui", 
                                     testclass="TestPlan", 
                                     testname=test_plan.name, 
                                     enabled="true")
        
        # Test plan properties
        string_prop = ET.SubElement(test_plan_elem, "stringProp", name="TestPlan.comments")
        string_prop.text = f"Generated test plan for {test_plan.base_url}"
        
        bool_prop = ET.SubElement(test_plan_elem, "boolProp", name="TestPlan.functional_mode")
        bool_prop.text = "false"
        
        bool_prop = ET.SubElement(test_plan_elem, "boolProp", name="TestPlan.tearDown_on_shutdown")
        bool_prop.text = "true"
        
        bool_prop = ET.SubElement(test_plan_elem, "boolProp", name="TestPlan.serialize_threadgroups")
        bool_prop.text = "false"
        
        element_prop = ET.SubElement(test_plan_elem, "elementProp", 
                                   name="TestPlan.arguments", 
                                   elementType="Arguments", 
                                   guiclass="ArgumentsPanel", 
                                   testclass="Arguments", 
                                   testname="User Defined Variables", 
                                   enabled="true")
        
        collection_prop = ET.SubElement(element_prop, "collectionProp", name="Arguments.arguments")
        
        string_prop = ET.SubElement(test_plan_elem, "stringProp", name="TestPlan.user_define_classpath")
        
        # Test plan hash tree
        test_plan_hash_tree = ET.SubElement(hash_tree, "hashTree")
        
        # Add thread groups
        for thread_group in test_plan.thread_groups:
            self._add_thread_group_to_xml(test_plan_hash_tree, thread_group, test_plan)
        
        # Convert to pretty string
        rough_string = ET.tostring(root, encoding='unicode')
        reparsed = minidom.parseString(rough_string)
        return reparsed.toprettyxml(indent="  ", encoding=None)
    
    def _add_thread_group_to_xml(self, parent: ET.Element, thread_group: JMeterThreadGroup, test_plan: JMeterTestPlan):
        """Add a thread group to the XML tree."""
        # Thread Group element
        tg_elem = ET.SubElement(parent, "ThreadGroup", 
                              guiclass="ThreadGroupGui", 
                              testclass="ThreadGroup", 
                              testname=thread_group.name, 
                              enabled="true")
        
        # Thread Group properties
        string_prop = ET.SubElement(tg_elem, "stringProp", name="ThreadGroup.on_sample_error")
        string_prop.text = "continue" if thread_group.continue_on_error else "stoptest"
        
        element_prop = ET.SubElement(tg_elem, "elementProp", 
                                   name="ThreadGroup.main_controller", 
                                   elementType="LoopController", 
                                   guiclass="LoopControlPanel", 
                                   testclass="LoopController", 
                                   testname="Loop Controller", 
                                   enabled="true")
        
        bool_prop = ET.SubElement(element_prop, "boolProp", name="LoopController.continue_forever")
        bool_prop.text = "false"
        
        string_prop = ET.SubElement(element_prop, "stringProp", name="LoopController.loops")
        string_prop.text = str(thread_group.loop_count)
        
        string_prop = ET.SubElement(tg_elem, "stringProp", name="ThreadGroup.num_threads")
        string_prop.text = str(thread_group.num_threads)
        
        string_prop = ET.SubElement(tg_elem, "stringProp", name="ThreadGroup.ramp_time")
        string_prop.text = str(thread_group.ramp_time)
        
        string_prop = ET.SubElement(tg_elem, "stringProp", name="ThreadGroup.start_time")
        string_prop.text = ""
        
        string_prop = ET.SubElement(tg_elem, "stringProp", name="ThreadGroup.end_time")
        string_prop.text = ""
        
        bool_prop = ET.SubElement(tg_elem, "boolProp", name="ThreadGroup.scheduler")
        bool_prop.text = "false"
        
        string_prop = ET.SubElement(tg_elem, "stringProp", name="ThreadGroup.duration")
        string_prop.text = ""
        
        string_prop = ET.SubElement(tg_elem, "stringProp", name="ThreadGroup.delay")
        string_prop.text = ""
        
        bool_prop = ET.SubElement(tg_elem, "boolProp", name="ThreadGroup.same_user_on_next_iteration")
        bool_prop.text = "true"
        
        # Thread Group hash tree
        tg_hash_tree = ET.SubElement(parent, "hashTree")
        
        # Add HTTP requests
        for http_request in thread_group.http_requests:
            self._add_http_request_to_xml(tg_hash_tree, http_request, test_plan)
        
        # Add listeners
        self._add_view_results_tree(tg_hash_tree)
        self._add_summary_report(tg_hash_tree)
    
    def _add_http_request_to_xml(self, parent: ET.Element, http_request: JMeterHttpRequest, test_plan: JMeterTestPlan):
        """Add an HTTP request to the XML tree."""
        # HTTP Request element
        http_elem = ET.SubElement(parent, "HTTPSamplerProxy", 
                                guiclass="HttpTestSampleGui", 
                                testclass="HTTPSamplerProxy", 
                                testname=http_request.name, 
                                enabled="true")
        
        # HTTP Request properties
        element_prop = ET.SubElement(http_elem, "elementProp", 
                                   name="HTTPsampler.Arguments", 
                                   elementType="Arguments", 
                                   guiclass="HTTPArgumentsPanel", 
                                   testclass="Arguments", 
                                   testname="User Defined Variables", 
                                   enabled="true")
        
        collection_prop = ET.SubElement(element_prop, "collectionProp", name="Arguments.arguments")
        
        # Add parameters
        for param in http_request.parameters:
            elem_prop = ET.SubElement(collection_prop, "elementProp", 
                                    name=param.name, 
                                    elementType="HTTPArgument")
            
            bool_prop = ET.SubElement(elem_prop, "boolProp", name="HTTPArgument.always_encode")
            bool_prop.text = str(param.url_encode).lower()
            
            string_prop = ET.SubElement(elem_prop, "stringProp", name="Argument.value")
            string_prop.text = param.value
            
            string_prop = ET.SubElement(elem_prop, "stringProp", name="Argument.metadata")
            string_prop.text = "="
            
            bool_prop = ET.SubElement(elem_prop, "boolProp", name="HTTPArgument.use_equals")
            bool_prop.text = "true"
            
            string_prop = ET.SubElement(elem_prop, "stringProp", name="Argument.name")
            string_prop.text = param.name
        
        string_prop = ET.SubElement(http_elem, "stringProp", name="HTTPSampler.domain")
        string_prop.text = test_plan.base_url
        
        string_prop = ET.SubElement(http_elem, "stringProp", name="HTTPSampler.port")
        string_prop.text = str(test_plan.port)
        
        string_prop = ET.SubElement(http_elem, "stringProp", name="HTTPSampler.protocol")
        string_prop.text = test_plan.protocol
        
        string_prop = ET.SubElement(http_elem, "stringProp", name="HTTPSampler.contentEncoding")
        string_prop.text = http_request.content_encoding
        
        string_prop = ET.SubElement(http_elem, "stringProp", name="HTTPSampler.path")
        string_prop.text = http_request.path
        
        string_prop = ET.SubElement(http_elem, "stringProp", name="HTTPSampler.method")
        string_prop.text = http_request.method.value
        
        bool_prop = ET.SubElement(http_elem, "boolProp", name="HTTPSampler.follow_redirects")
        bool_prop.text = str(http_request.follow_redirects).lower()
        
        bool_prop = ET.SubElement(http_elem, "boolProp", name="HTTPSampler.auto_redirects")
        bool_prop.text = "false"
        
        bool_prop = ET.SubElement(http_elem, "boolProp", name="HTTPSampler.use_keepalive")
        bool_prop.text = str(http_request.use_keepalive).lower()
        
        bool_prop = ET.SubElement(http_elem, "boolProp", name="HTTPSampler.DO_MULTIPART_POST")
        bool_prop.text = "false"
        
        string_prop = ET.SubElement(http_elem, "stringProp", name="HTTPSampler.embedded_url_re")
        string_prop.text = ""
        
        string_prop = ET.SubElement(http_elem, "stringProp", name="HTTPSampler.connect_timeout")
        string_prop.text = ""
        
        string_prop = ET.SubElement(http_elem, "stringProp", name="HTTPSampler.response_timeout")
        string_prop.text = ""
        
        # Add body data if present
        if http_request.body_data:
            bool_prop = ET.SubElement(http_elem, "boolProp", name="HTTPSampler.postBodyRaw")
            bool_prop.text = "true"
            
            element_prop = ET.SubElement(http_elem, "elementProp", 
                                       name="HTTPsampler.Arguments", 
                                       elementType="Arguments")
            
            collection_prop = ET.SubElement(element_prop, "collectionProp", name="Arguments.arguments")
            
            elem_prop = ET.SubElement(collection_prop, "elementProp", 
                                    name="", 
                                    elementType="HTTPArgument")
            
            string_prop = ET.SubElement(elem_prop, "stringProp", name="Argument.value")
            string_prop.text = http_request.body_data
        
        # HTTP Request hash tree
        http_hash_tree = ET.SubElement(parent, "hashTree")
        
        # Add HTTP Header Manager if headers exist
        if http_request.headers:
            self._add_header_manager_to_xml(http_hash_tree, http_request.headers)
    
    def _add_header_manager_to_xml(self, parent: ET.Element, headers: List[JMeterHeader]):
        """Add HTTP Header Manager to the XML tree."""
        header_elem = ET.SubElement(parent, "HeaderManager", 
                                  guiclass="HeaderPanel", 
                                  testclass="HeaderManager", 
                                  testname="HTTP Header Manager", 
                                  enabled="true")
        
        collection_prop = ET.SubElement(header_elem, "collectionProp", name="HeaderManager.headers")
        
        for header in headers:
            elem_prop = ET.SubElement(collection_prop, "elementProp", 
                                    name="", 
                                    elementType="Header")
            
            string_prop = ET.SubElement(elem_prop, "stringProp", name="Header.name")
            string_prop.text = header.name
            
            string_prop = ET.SubElement(elem_prop, "stringProp", name="Header.value")
            string_prop.text = header.value
        
        # Header Manager hash tree
        ET.SubElement(parent, "hashTree")
    
    def _add_view_results_tree(self, parent: ET.Element):
        """Add View Results Tree listener."""
        listener_elem = ET.SubElement(parent, "ResultCollector", 
                                     guiclass="ViewResultsFullVisualizer", 
                                     testclass="ResultCollector", 
                                     testname="View Results Tree", 
                                     enabled="true")
        
        bool_prop = ET.SubElement(listener_elem, "boolProp", name="ResultCollector.error_logging")
        bool_prop.text = "false"
        
        obj_prop = ET.SubElement(listener_elem, "objProp")
        name_elem = ET.SubElement(obj_prop, "name")
        name_elem.text = "saveConfig"
        
        value_elem = ET.SubElement(obj_prop, "value", {"class": "SampleSaveConfiguration"})
        
        # Save configuration properties
        for prop_name, prop_value in [
            ("time", "true"), ("latency", "true"), ("timestamp", "true"),
            ("success", "true"), ("label", "true"), ("code", "true"),
            ("message", "true"), ("threadName", "true"), ("dataType", "true"),
            ("encoding", "false"), ("assertions", "true"), ("subresults", "true"),
            ("responseData", "false"), ("samplerData", "false"), ("xml", "false"),
            ("fieldNames", "true"), ("responseHeaders", "false"), ("requestHeaders", "false"),
            ("responseDataOnError", "false"), ("saveAssertionResultsFailureMessage", "true"),
            ("assertionsResultsToSave", "0"), ("bytes", "true"), ("sentBytes", "true"),
            ("url", "true"), ("threadCounts", "true"), ("idleTime", "true"),
            ("connectTime", "true")
        ]:
            prop_elem = ET.SubElement(value_elem, prop_name)
            prop_elem.text = prop_value
        
        string_prop = ET.SubElement(listener_elem, "stringProp", name="filename")
        string_prop.text = ""
        
        # Listener hash tree
        ET.SubElement(parent, "hashTree")
    
    def _add_summary_report(self, parent: ET.Element):
        """Add Summary Report listener."""
        listener_elem = ET.SubElement(parent, "ResultCollector", 
                                     guiclass="SummaryReport", 
                                     testclass="ResultCollector", 
                                     testname="Summary Report", 
                                     enabled="true")
        
        bool_prop = ET.SubElement(listener_elem, "boolProp", name="ResultCollector.error_logging")
        bool_prop.text = "false"
        
        obj_prop = ET.SubElement(listener_elem, "objProp")
        name_elem = ET.SubElement(obj_prop, "name")
        name_elem.text = "saveConfig"
        
        value_elem = ET.SubElement(obj_prop, "value", {"class": "SampleSaveConfiguration"})
        
        # Save configuration properties for summary
        for prop_name, prop_value in [
            ("time", "true"), ("latency", "true"), ("timestamp", "true"),
            ("success", "true"), ("label", "true"), ("code", "true"),
            ("message", "true"), ("threadName", "true"), ("dataType", "true"),
            ("encoding", "false"), ("assertions", "true"), ("subresults", "true"),
            ("responseData", "false"), ("samplerData", "false"), ("xml", "false"),
            ("fieldNames", "true"), ("responseHeaders", "false"), ("requestHeaders", "false"),
            ("responseDataOnError", "false"), ("saveAssertionResultsFailureMessage", "true"),
            ("assertionsResultsToSave", "0"), ("bytes", "true"), ("sentBytes", "true"),
            ("url", "true"), ("threadCounts", "true"), ("idleTime", "true"),
            ("connectTime", "true")
        ]:
            prop_elem = ET.SubElement(value_elem, prop_name)
            prop_elem.text = prop_value
        
        string_prop = ET.SubElement(listener_elem, "stringProp", name="filename")
        string_prop.text = ""
        
        # Listener hash tree
        ET.SubElement(parent, "hashTree")