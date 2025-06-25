import asyncio
import logging
from typing import Dict, Any, Optional, List
import openai
from anthropic import Anthropic
from src.utils.config import ConfigManager

logger = logging.getLogger(__name__)

class AIAnalysisEngine:
    """AI-powered analysis engine for test results using OpenAI or Anthropic."""
    
    def __init__(self, config: ConfigManager):
        self.config = config
        self.openai_client = None
        self.anthropic_client = None
        self._initialize_clients()
    
    def _initialize_clients(self):
        """Initialize AI clients based on configuration."""
        try:
            ai_creds = self.config.get_credentials("ai")
            if self.config.config.get("ai_provider", "openai") == "openai" and ai_creds.get("openai_api_key"):
                self.openai_client = openai.OpenAI(api_key=ai_creds["openai_api_key"])
                logger.info("OpenAI client initialized")
            elif self.config.config.get("ai_provider", "anthropic") == "anthropic" and ai_creds.get("anthropic_api_key"):
                self.anthropic_client = Anthropic(api_key=ai_creds["anthropic_api_key"])
                logger.info("Anthropic client initialized")
        except Exception as e:
            logger.error(f"Failed to initialize AI client: {e}")
    
    async def analyze_results(self, test_results: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze test results using AI and return insights."""
        try:
            if self.openai_client:
                return await self._analyze_with_openai(test_results)
            elif self.anthropic_client:
                return await self._analyze_with_anthropic(test_results)
            else:
                return self._basic_analysis(test_results)
        except Exception as e:
            logger.error(f"AI analysis failed: {e}")
            return self._basic_analysis(test_results)
    
    async def _analyze_with_openai(self, test_results: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze results using OpenAI API."""
        try:
            if not self.openai_client:
                return self._basic_analysis(test_results)
                
            prompt = self._create_analysis_prompt(test_results)
            
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a performance testing expert analyzing load test results."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.3
            )
            
            analysis = response.choices[0].message.content or ""
            
            return {
                "provider": "openai",
                "summary": f"AI analysis of {test_results.get('test_name', 'Test')}",
                "key_findings": self._extract_findings(analysis),
                "risk_level": self._assess_risk(test_results),
                "risk_description": self._extract_risk_description(analysis),
                "recommendations": self._extract_recommendations(analysis),
                "full_analysis": analysis
            }
        except Exception as e:
            logger.error(f"OpenAI API call failed: {e}")
            return self._basic_analysis(test_results)
    
    async def _analyze_with_anthropic(self, test_results: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze results using Anthropic API."""
        try:
            if not self.anthropic_client:
                return self._basic_analysis(test_results)
                
            prompt = self._create_analysis_prompt(test_results)
            
            response = self.anthropic_client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=1000,
                temperature=0.3,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            analysis = response.content[0].text if response.content else ""
            
            return {
                "provider": "anthropic",
                "summary": f"AI analysis of {test_results.get('test_name', 'Test')}",
                "key_findings": self._extract_findings(analysis),
                "risk_level": self._assess_risk(test_results),
                "risk_description": self._extract_risk_description(analysis),
                "recommendations": self._extract_recommendations(analysis),
                "full_analysis": analysis
            }
        except Exception as e:
            logger.error(f"Anthropic API call failed: {e}")
            return self._basic_analysis(test_results)
    
    def _create_analysis_prompt(self, test_results: Dict[str, Any]) -> str:
        """Create a prompt for AI analysis."""
        return f"""
        Analyze the following performance test results and provide insights:
        
        Test Name: {test_results.get('test_name', 'Unknown')}
        Duration: {test_results.get('duration', 0)} seconds
        Total Requests: {test_results.get('total_requests', 0)}
        Successful Requests: {test_results.get('successful_requests', 0)}
        Failed Requests: {test_results.get('failed_requests', 0)}
        Average Response Time: {test_results.get('avg_response_time', 0)} seconds
        Throughput: {test_results.get('throughput', 0)} requests/second
        
        Please provide:
        1. Key findings and insights
        2. Performance assessment
        3. Risk level (LOW/MEDIUM/HIGH)
        4. Recommendations for improvement
        5. Any potential issues or bottlenecks
        """
    
    def _basic_analysis(self, test_results: Dict[str, Any]) -> Dict[str, Any]:
        """Provide basic analysis when AI is not available."""
        total_requests = test_results.get('total_requests', 0)
        successful_requests = test_results.get('successful_requests', 0)
        failed_requests = test_results.get('failed_requests', 0)
        avg_response_time = test_results.get('avg_response_time', 0)
        
        success_rate = (successful_requests / total_requests * 100) if total_requests > 0 else 0
        
        return {
            "provider": "basic_analysis",
            "summary": f"Basic analysis of {test_results.get('test_name', 'Test')}",
            "key_findings": [
                f"Total requests: {total_requests}",
                f"Success rate: {success_rate:.1f}%",
                f"Average response time: {avg_response_time:.3f}s"
            ],
            "risk_level": self._assess_risk(test_results),
            "risk_description": "Basic performance assessment completed"
        }
    
    def _assess_risk(self, test_results: Dict[str, Any]) -> str:
        """Assess risk level based on test results."""
        failed_requests = test_results.get('failed_requests', 0)
        total_requests = test_results.get('total_requests', 0)
        avg_response_time = test_results.get('avg_response_time', 0)
        
        if total_requests == 0:
            return "UNKNOWN"
        
        failure_rate = failed_requests / total_requests
        
        if failure_rate > 0.1 or avg_response_time > 5.0:
            return "HIGH"
        elif failure_rate > 0.05 or avg_response_time > 2.0:
            return "MEDIUM"
        else:
            return "LOW"
    
    def _extract_findings(self, analysis: str) -> List[str]:
        """Extract key findings from AI analysis."""
        # Simple extraction - in a real implementation, you might use more sophisticated parsing
        lines = analysis.split('\n')
        findings = []
        for line in lines:
            if any(keyword in line.lower() for keyword in ['finding', 'insight', 'observation', '•', '-']):
                findings.append(line.strip())
        return findings[:5]  # Limit to 5 findings
    
    def _extract_risk_description(self, analysis: str) -> str:
        """Extract risk description from AI analysis."""
        if 'risk' in analysis.lower():
            lines = analysis.split('\n')
            for line in lines:
                if 'risk' in line.lower():
                    return line.strip()
        return "Risk assessment based on performance metrics"
    
    def _extract_recommendations(self, analysis: str) -> List[str]:
        """Extract recommendations from AI analysis."""
        lines = analysis.split('\n')
        recommendations = []
        for line in lines:
            if any(keyword in line.lower() for keyword in ['recommend', 'suggest', 'improve', 'optimize']):
                recommendations.append(line.strip())
        return recommendations[:3]  # Limit to 3 recommendations 