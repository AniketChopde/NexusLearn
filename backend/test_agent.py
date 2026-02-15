import asyncio
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.getcwd()))

from agents.course_recommendation_agent import course_recommendation_agent

async def main():
    print("Testing Course Recommendation Agent...")
    try:
        courses = await course_recommendation_agent.recommend_courses(
            exam_type="Java",
            current_knowledge={}
        )
        print(f"Found {len(courses)} courses:")
        for c in courses:
            print(f"- {c['title']} ({c['platform']}): {c['url']}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
