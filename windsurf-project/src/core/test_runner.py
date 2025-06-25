"""
Test runner for orchestrating test execution
"""

import asyncio
import time
from typing import Dict, List, Any, Optional
from datetime import datetime

from utils.logger import get_logger, TestLogger
from utils.config import ConfigManager
from core.test_engine import TestEngine


class TestRunner:
    """Orchestrates test execution and manages results"""
    
    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.logger = get_logger("nlm.runner")
        self.test_engine = TestEngine(config_manager)
        self.current_test = None
    
    async def run_test(self, test_config: Dict[str, Any]) -> Dict[str, Any]:
        """Run a complete test with the given configuration and return a dict as expected by tests."""
        start_time = time.time()
        test_name = test_config.get('test_name', 'Unnamed Test')
        self.logger.info(f"Starting test: {test_name}")
        test_logger = TestLogger(test_name)
        try:
            self.current_test = test_config
            self.test_engine.running = True
            results = await self._execute_test_async(test_config)
            duration = time.time() - start_time
            summary = self.test_engine.get_results_summary(results)
            summary.update({
                'test_name': test_name,
                'duration': duration,
                'start_time': start_time,
                'end_time': time.time(),
                'timestamp': datetime.now().isoformat(),
                'results': results
            })
            test_logger.log_summary(
                summary['total_requests'],
                summary['successful_requests'],
                summary['failed_requests'],
                summary['avg_response_time']
            )
            self.logger.info(f"Test completed: {test_name}")
            return summary
        except ValueError as ve:
            # Re-raise ValueError for unsupported target type so test can catch it
            raise ve
        except Exception as e:
            self.logger.error(f"Test failed: {e}")
            return {
                'test_name': test_name,
                'duration': time.time() - start_time,
                'error': str(e),
                'total_requests': 0,
                'successful_requests': 0,
                'failed_requests': 0,
                'avg_response_time': 0,
                'throughput': 0,
                'results': []
            }
        finally:
            self.current_test = None
            self.test_engine.running = False
    
    def run_test_sync(self, test_config: Dict[str, Any]) -> Dict[str, Any]:
        """Synchronous wrapper for run_test"""
        start_time = time.time()
        test_name = test_config.get('test_name', 'Unnamed Test')
        
        self.logger.info(f"Starting test: {test_name}")
        
        # Create test logger
        test_logger = TestLogger(test_name)
        
        try:
            # Set test as running
            self.current_test = test_config
            self.test_engine.running = True
            
            # Run the test asynchronously
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                results = loop.run_until_complete(
                    self._execute_test_async(test_config)
                )
            finally:
                loop.close()
            
            # Calculate test duration
            duration = time.time() - start_time
            
            # Generate summary
            summary = self.test_engine.get_results_summary(results)
            summary.update({
                'test_name': test_name,
                'duration': duration,
                'start_time': start_time,
                'end_time': time.time(),
                'timestamp': datetime.now().isoformat()
            })
            
            # Log summary
            test_logger.log_summary(
                summary['total_requests'],
                summary['successful_requests'],
                summary['failed_requests'],
                summary['avg_response_time']
            )
            
            self.logger.info(f"Test completed: {test_name}")
            return summary
            
        except Exception as e:
            self.logger.error(f"Test failed: {e}")
            return {
                'test_name': test_name,
                'duration': time.time() - start_time,
                'error': str(e),
                'total_requests': 0,
                'successful_requests': 0,
                'failed_requests': 0,
                'avg_response_time': 0,
                'throughput': 0
            }
        finally:
            self.current_test = None
            self.test_engine.running = False
    
    async def _execute_test_async(self, test_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Execute test asynchronously"""
        targets = test_config.get('targets', [])
        load_profile = test_config.get('load_profile', {})
        all_results = []
        for target in targets:
            target_type = target.get('type', 'http')
            if target_type == 'http':
                results = await self.test_engine.execute_http_test(target, load_profile)
            elif target_type == 'database':
                results = await self.test_engine.execute_database_test(target, load_profile)
            elif target_type == 'message_queue':
                results = await self.test_engine.execute_message_queue_test(target, load_profile)
            else:
                self.logger.warning(f"Unknown target type: {target_type}")
                raise ValueError("Unsupported target type")
            all_results.extend(results)
        return all_results
    
    def stop_current_test(self):
        """Stop the currently running test"""
        if self.current_test:
            self.test_engine.stop()
            self.logger.info("Test stop requested")
        else:
            self.logger.info("No test currently running")
    
    def stop_test(self):
        """Stop the currently running test (alias for stop_current_test)"""
        if self.current_test:
            self.test_engine.stop()
            self.current_test = None
            self.logger.info("Test stop requested")
        else:
            self.logger.info("No test currently running")
    
    def get_test_status(self) -> Dict[str, Any]:
        """Get status of current test"""
        if self.current_test:
            if isinstance(self.current_test, dict):
                return {
                    'running': self.test_engine.running,
                    'test_name': self.current_test.get('test_name', 'Unknown'),
                    'current_test': self.current_test,
                    'targets': len(self.current_test.get('targets', [])),
                    'load_profile': self.current_test.get('load_profile', {})
                }
            else:
                # Handle case where current_test is a string
                return {
                    'running': self.test_engine.running,
                    'test_name': str(self.current_test),
                    'current_test': self.current_test,
                    'targets': 0,
                    'load_profile': {}
                }
        else:
            return {
                'running': False,
                'test_name': None,
                'current_test': None,
                'targets': 0,
                'load_profile': {}
            } 