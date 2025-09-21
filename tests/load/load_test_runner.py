"""
Load test runner with custom scenarios and metrics collection.
"""
import asyncio
import aiohttp
import time
import statistics
from typing import List, Dict, Any
import json


class LoadTestRunner:
    """Custom load test runner for detailed performance testing."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.results = []
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def register_user(self, username: str, password: str) -> Dict[str, Any]:
        """Register a new user."""
        start_time = time.time()
        try:
            async with self.session.post(
                f"{self.base_url}/api/users/register",
                json={"username": username, "password": password}
            ) as response:
                end_time = time.time()
                return {
                    "action": "register",
                    "status_code": response.status,
                    "response_time": end_time - start_time,
                    "success": response.status == 200
                }
        except Exception as e:
            return {
                "action": "register",
                "status_code": 0,
                "response_time": time.time() - start_time,
                "success": False,
                "error": str(e)
            }
    
    async def login_user(self, username: str, password: str) -> Dict[str, Any]:
        """Login user and return token."""
        start_time = time.time()
        try:
            async with self.session.post(
                f"{self.base_url}/api/users/login",
                json={"username": username, "password": password}
            ) as response:
                end_time = time.time()
                data = await response.json() if response.status == 200 else {}
                return {
                    "action": "login",
                    "status_code": response.status,
                    "response_time": end_time - start_time,
                    "success": response.status == 200,
                    "token": data.get("access_token")
                }
        except Exception as e:
            return {
                "action": "login",
                "status_code": 0,
                "response_time": time.time() - start_time,
                "success": False,
                "error": str(e)
            }
    
    async def send_message(self, token: str, chat_id: int, content: str) -> Dict[str, Any]:
        """Send a message to a chat."""
        start_time = time.time()
        headers = {"Authorization": f"Bearer {token}"}
        try:
            async with self.session.post(
                f"{self.base_url}/api/messages/",
                json={"chat_id": chat_id, "content": content},
                headers=headers
            ) as response:
                end_time = time.time()
                return {
                    "action": "send_message",
                    "status_code": response.status,
                    "response_time": end_time - start_time,
                    "success": response.status == 200
                }
        except Exception as e:
            return {
                "action": "send_message",
                "status_code": 0,
                "response_time": time.time() - start_time,
                "success": False,
                "error": str(e)
            }
    
    async def get_messages(self, token: str, chat_id: int) -> Dict[str, Any]:
        """Get messages from a chat."""
        start_time = time.time()
        headers = {"Authorization": f"Bearer {token}"}
        try:
            async with self.session.get(
                f"{self.base_url}/api/messages/{chat_id}",
                headers=headers
            ) as response:
                end_time = time.time()
                return {
                    "action": "get_messages",
                    "status_code": response.status,
                    "response_time": end_time - start_time,
                    "success": response.status == 200
                }
        except Exception as e:
            return {
                "action": "get_messages",
                "status_code": 0,
                "response_time": time.time() - start_time,
                "success": False,
                "error": str(e)
            }
    
    async def create_chat(self, token: str, name: str) -> Dict[str, Any]:
        """Create a new chat."""
        start_time = time.time()
        headers = {"Authorization": f"Bearer {token}"}
        try:
            async with self.session.post(
                f"{self.base_url}/api/chats/",
                params={"name": name},
                headers=headers
            ) as response:
                end_time = time.time()
                data = await response.json() if response.status == 200 else {}
                return {
                    "action": "create_chat",
                    "status_code": response.status,
                    "response_time": end_time - start_time,
                    "success": response.status == 200,
                    "chat_id": data.get("id")
                }
        except Exception as e:
            return {
                "action": "create_chat",
                "status_code": 0,
                "response_time": time.time() - start_time,
                "success": False,
                "error": str(e)
            }
    
    async def simulate_user_session(self, user_id: int, num_actions: int = 10) -> List[Dict[str, Any]]:
        """Simulate a complete user session."""
        username = f"loadtest_user_{user_id}"
        password = "loadtest_password_123"
        session_results = []
        
        # Register user
        register_result = await self.register_user(username, password)
        session_results.append(register_result)
        
        if not register_result["success"]:
            return session_results
        
        # Login user
        login_result = await self.login_user(username, password)
        session_results.append(login_result)
        
        if not login_result["success"]:
            return session_results
        
        token = login_result["token"]
        
        # Create a chat
        chat_result = await self.create_chat(token, f"Load Test Chat {user_id}")
        session_results.append(chat_result)
        
        if not chat_result["success"]:
            return session_results
        
        chat_id = chat_result["chat_id"]
        
        # Perform random actions
        for i in range(num_actions):
            action = await self.perform_random_action(token, chat_id, user_id, i)
            session_results.append(action)
        
        return session_results
    
    async def perform_random_action(self, token: str, chat_id: int, user_id: int, action_id: int) -> Dict[str, Any]:
        """Perform a random action."""
        import random
        
        actions = [
            ("send_message", lambda: self.send_message(token, chat_id, f"Message {action_id} from user {user_id}")),
            ("get_messages", lambda: self.get_messages(token, chat_id)),
        ]
        
        action_name, action_func = random.choice(actions)
        result = await action_func()
        result["action"] = action_name
        return result
    
    async def run_concurrent_users(self, num_users: int, actions_per_user: int = 10) -> Dict[str, Any]:
        """Run load test with concurrent users."""
        print(f"Starting load test with {num_users} concurrent users...")
        
        start_time = time.time()
        
        # Create tasks for all users
        tasks = [
            self.simulate_user_session(user_id, actions_per_user)
            for user_id in range(num_users)
        ]
        
        # Run all tasks concurrently
        all_results = await asyncio.gather(*tasks)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Flatten results
        flat_results = []
        for user_results in all_results:
            flat_results.extend(user_results)
        
        # Calculate statistics
        stats = self.calculate_statistics(flat_results, total_time)
        
        return {
            "test_config": {
                "num_users": num_users,
                "actions_per_user": actions_per_user,
                "total_actions": len(flat_results)
            },
            "duration": total_time,
            "statistics": stats,
            "raw_results": flat_results
        }
    
    def calculate_statistics(self, results: List[Dict[str, Any]], total_time: float) -> Dict[str, Any]:
        """Calculate performance statistics."""
        if not results:
            return {}
        
        # Group by action type
        by_action = {}
        for result in results:
            action = result["action"]
            if action not in by_action:
                by_action[action] = []
            by_action[action].append(result)
        
        stats = {
            "overall": {
                "total_requests": len(results),
                "successful_requests": sum(1 for r in results if r["success"]),
                "failed_requests": sum(1 for r in results if not r["success"]),
                "success_rate": sum(1 for r in results if r["success"]) / len(results) * 100,
                "requests_per_second": len(results) / total_time,
                "total_duration": total_time
            }
        }
        
        # Calculate per-action statistics
        for action, action_results in by_action.items():
            response_times = [r["response_time"] for r in action_results]
            successful_results = [r for r in action_results if r["success"]]
            
            stats[action] = {
                "count": len(action_results),
                "success_count": len(successful_results),
                "success_rate": len(successful_results) / len(action_results) * 100,
                "avg_response_time": statistics.mean(response_times),
                "min_response_time": min(response_times),
                "max_response_time": max(response_times),
                "median_response_time": statistics.median(response_times),
                "p95_response_time": self.percentile(response_times, 95),
                "p99_response_time": self.percentile(response_times, 99)
            }
        
        return stats
    
    def percentile(self, data: List[float], percentile: int) -> float:
        """Calculate percentile of data."""
        if not data:
            return 0
        sorted_data = sorted(data)
        index = int(len(sorted_data) * percentile / 100)
        return sorted_data[min(index, len(sorted_data) - 1)]
    
    def print_report(self, test_results: Dict[str, Any]):
        """Print a formatted test report."""
        print("\n" + "="*60)
        print("LOAD TEST REPORT")
        print("="*60)
        
        config = test_results["test_config"]
        print(f"Configuration:")
        print(f"  Users: {config['num_users']}")
        print(f"  Actions per user: {config['actions_per_user']}")
        print(f"  Total actions: {config['total_actions']}")
        print(f"  Duration: {test_results['duration']:.2f} seconds")
        
        stats = test_results["statistics"]
        overall = stats["overall"]
        print(f"\nOverall Performance:")
        print(f"  Requests per second: {overall['requests_per_second']:.2f}")
        print(f"  Success rate: {overall['success_rate']:.2f}%")
        print(f"  Failed requests: {overall['failed_requests']}")
        
        print(f"\nPer-Action Statistics:")
        for action, action_stats in stats.items():
            if action == "overall":
                continue
            
            print(f"  {action.upper()}:")
            print(f"    Count: {action_stats['count']}")
            print(f"    Success rate: {action_stats['success_rate']:.2f}%")
            print(f"    Avg response time: {action_stats['avg_response_time']:.3f}s")
            print(f"    P95 response time: {action_stats['p95_response_time']:.3f}s")
            print(f"    P99 response time: {action_stats['p99_response_time']:.3f}s")


async def run_load_tests():
    """Run various load test scenarios."""
    async with LoadTestRunner() as runner:
        # Light load test
        print("Running light load test (10 users)...")
        light_results = await runner.run_concurrent_users(10, 5)
        runner.print_report(light_results)
        
        # Medium load test
        print("\nRunning medium load test (50 users)...")
        medium_results = await runner.run_concurrent_users(50, 10)
        runner.print_report(medium_results)
        
        # Heavy load test
        print("\nRunning heavy load test (100 users)...")
        heavy_results = await runner.run_concurrent_users(100, 15)
        runner.print_report(heavy_results)
        
        # Save results to file
        all_results = {
            "light_load": light_results,
            "medium_load": medium_results,
            "heavy_load": heavy_results
        }
        
        with open("load_test_results.json", "w") as f:
            json.dump(all_results, f, indent=2, default=str)
        
        print(f"\nResults saved to load_test_results.json")


if __name__ == "__main__":
    asyncio.run(run_load_tests())
