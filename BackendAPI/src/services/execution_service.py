import os
import subprocess
import tempfile
from typing import Dict, Any, List
from datetime import datetime
import uuid
import json
import logging

from ..database.models import TestCase, TestScript, RunHistory, ExecutionStatus
from ..database.connection import get_db_context
from .minio_service import minio_service

logger = logging.getLogger(__name__)

class ExecutionService:
    """Service for executing Robot Framework test cases."""
    
    def __init__(self):
        self.temp_dir = tempfile.gettempdir()
    
    # PUBLIC_INTERFACE
    async def execute_test_case(self, case_id: str, user_id: str, config: Dict[str, Any] = None) -> str:
        """
        Execute a single test case.
        
        Args:
            case_id: ID of the test case to execute
            user_id: ID of the user executing the test
            config: Optional execution configuration
            
        Returns:
            Run history ID for tracking the execution
        """
        with get_db_context() as db:
            # Get test case and script
            test_case = db.query(TestCase).filter(TestCase.id == case_id).first()
            if not test_case:
                raise ValueError(f"Test case {case_id} not found")
            
            test_script = db.query(TestScript).filter(TestScript.id == test_case.test_script_id).first()
            if not test_script:
                raise ValueError(f"Test script for case {case_id} not found")
            
            # Create run history record
            run_id = str(uuid.uuid4())
            run_history = RunHistory(
                id=run_id,
                case_id=case_id,
                status=ExecutionStatus.RUNNING,
                executed_by=user_id,
                started_at=datetime.utcnow()
            )
            db.add(run_history)
            db.commit()
        
        # Execute test in background
        try:
            result = await self._run_robot_test(test_script, test_case, run_id, config)
            await self._update_run_result(run_id, result)
        except Exception as e:
            logger.error(f"Error executing test case {case_id}: {e}")
            await self._update_run_result(run_id, {
                "status": ExecutionStatus.FAILED,
                "error": str(e)
            })
        
        return run_id
    
    # PUBLIC_INTERFACE
    async def execute_multiple_test_cases(self, case_ids: List[str], user_id: str, config: Dict[str, Any] = None) -> List[str]:
        """
        Execute multiple test cases.
        
        Args:
            case_ids: List of test case IDs to execute
            user_id: ID of the user executing the tests
            config: Optional execution configuration
            
        Returns:
            List of run history IDs for tracking the executions
        """
        run_ids = []
        for case_id in case_ids:
            try:
                run_id = await self.execute_test_case(case_id, user_id, config)
                run_ids.append(run_id)
            except Exception as e:
                logger.error(f"Failed to start execution for case {case_id}: {e}")
        
        return run_ids
    
    async def _run_robot_test(self, test_script: TestScript, test_case: TestCase, run_id: str, config: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Execute Robot Framework test and return results.
        
        Args:
            test_script: The test script to execute
            test_case: The test case to execute
            run_id: Run history ID
            config: Execution configuration
            
        Returns:
            Execution results
        """
        # Create temporary files for execution
        script_path = os.path.join(self.temp_dir, f"script_{run_id}.robot")
        output_dir = os.path.join(self.temp_dir, f"output_{run_id}")
        os.makedirs(output_dir, exist_ok=True)
        
        try:
            # Write script content to file
            with open(script_path, 'w') as f:
                f.write(test_script.content or "")
            
            # Prepare Robot Framework command
            cmd = [
                "robot",
                "--outputdir", output_dir,
                "--output", "output.xml",
                "--log", "log.html",
                "--report", "report.html"
            ]
            
            # Add variables from test case configuration
            if test_case.variables:
                for key, value in test_case.variables.items():
                    cmd.extend(["--variable", f"{key}:{value}"])
            
            # Add custom configuration
            if config:
                for key, value in config.items():
                    if key.startswith("--"):
                        cmd.extend([key, str(value)])
            
            cmd.append(script_path)
            
            # Execute Robot Framework
            logger.info(f"Executing Robot Framework test: {' '.join(cmd)}")
            start_time = datetime.utcnow()
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=3600  # 1 hour timeout
            )
            
            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()
            
            # Process results
            execution_result = {
                "status": ExecutionStatus.COMPLETED if result.returncode == 0 else ExecutionStatus.FAILED,
                "return_code": result.returncode,
                "duration": duration,
                "stdout": result.stdout,
                "stderr": result.stderr
            }
            
            # Upload log files to MinIO
            log_files = {}
            for filename in ["output.xml", "log.html", "report.html"]:
                file_path = os.path.join(output_dir, filename)
                if os.path.exists(file_path):
                    object_name = f"logs/{run_id}/{filename}"
                    with open(file_path, 'rb') as f:
                        minio_service.upload_file(f, object_name)
                    log_files[filename] = object_name
            
            execution_result["log_files"] = log_files
            
            return execution_result
            
        except subprocess.TimeoutExpired:
            return {
                "status": ExecutionStatus.FAILED,
                "error": "Test execution timed out"
            }
        except Exception as e:
            return {
                "status": ExecutionStatus.FAILED,
                "error": str(e)
            }
        finally:
            # Cleanup temporary files
            try:
                if os.path.exists(script_path):
                    os.remove(script_path)
                if os.path.exists(output_dir):
                    import shutil
                    shutil.rmtree(output_dir)
            except Exception as e:
                logger.warning(f"Failed to cleanup temporary files: {e}")
    
    async def _update_run_result(self, run_id: str, result: Dict[str, Any]):
        """Update run history with execution result."""
        with get_db_context() as db:
            run_history = db.query(RunHistory).filter(RunHistory.id == run_id).first()
            if run_history:
                run_history.status = result.get("status", ExecutionStatus.FAILED)
                run_history.finished_at = datetime.utcnow()
                run_history.results = result
                
                if "error" in result:
                    run_history.error_message = result["error"]
                
                if "log_files" in result:
                    run_history.log_file_path = json.dumps(result["log_files"])
                
                db.commit()

# Global instance
execution_service = ExecutionService()
