"""
Architecture Ideation Tool
Manages the iterative process of architecture design with AI feedback.

Workflow:
1. Load current architecture document (if exists)
2. Load user's new architectural thoughts
3. Send to LLM for analysis and suggestions
4. Present feedback to user
5. User refines and repeats until satisfied
6. Output finalized architecture requirement document
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime

from ..shared.llm_client import LLMClient
from ..shared.state_manager import StateManager
from ..shared.logger import get_logger

logger = get_logger(__name__)


@dataclass
class ArchitectureThought:
    """A single architectural thought/requirement."""
    id: str
    content: str
    category: str  # 'module', 'package', 'interface', 'data_flow', 'dependency'
    priority: int  # 1-5
    status: str  # 'proposed', 'accepted', 'rejected', 'implemented'
    created_at: datetime = field(default_factory=datetime.now)
    ai_feedback: Optional[str] = None
    user_response: Optional[str] = None
    related_thoughts: List[str] = field(default_factory=list)


@dataclass
class ArchitectureDocument:
    """Complete architecture requirement document."""
    version: int
    project_name: str
    overview: str
    modules: List[Dict[str, Any]]
    packages: List[Dict[str, Any]]
    dependencies: Dict[str, List[str]]
    data_flow: Dict[str, Any]
    thoughts: List[ArchitectureThought]
    history: List[Dict[str, Any]]
    finalized_at: Optional[datetime] = None


class ArchitectureIdeator:
    """
    AI-assisted architecture ideation and refinement tool.
    
    Features:
    - Load/save architecture documents
    - Analyze architectural thoughts with AI
    - Suggest complementary modules/packages
    - Identify potential issues (circular deps, coupling)
    - Generate Mermaid diagrams
    - Maintain decision history
    """
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.llm = LLMClient()
        self.state = StateManager(project_root / ".ai_state" / "arch_ideator.json")
        
        self.doc_path = project_root / "project_doc" / "architecture"
        self.doc_path.mkdir(parents=True, exist_ok=True)
        
        self.history_path = self.doc_path / "history"
        self.history_path.mkdir(exist_ok=True)
        
        self.current_doc: Optional[ArchitectureDocument] = None
    
    def load_or_create_document(self, project_name: str) -> ArchitectureDocument:
        """Load existing architecture document or create new one."""
        doc_file = self.doc_path / "current" / "architecture.json"
        
        if doc_file.exists():
            with open(doc_file, 'r') as f:
                data = json.load(f)
            return ArchitectureDocument(**data)
        
        return ArchitectureDocument(
            version=1,
            project_name=project_name,
            overview="",
            modules=[],
            packages=[],
            dependencies={},
            data_flow={},
            thoughts=[],
            history=[]
        )
    
    def add_thought(self, content: str, category: str, priority: int = 3) -> ArchitectureThought:
        """Add a new architectural thought."""
        thought = ArchitectureThought(
            id=f"thought_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self.current_doc.thoughts)}",
            content=content,
            category=category,
            priority=priority,
            status='proposed'
        )
        
        # Get AI feedback on the thought
        feedback = self._get_ai_feedback(thought)
        thought.ai_feedback = feedback
        
        self.current_doc.thoughts.append(thought)
        return thought
    
    def _get_ai_feedback(self, thought: ArchitectureThought) -> str:
        """Get AI analysis and suggestions for a thought."""
        prompt = f"""
        Analyze this architectural thought for a Python project:
        
        Category: {thought.category}
        Content: {thought.content}
        
        Current modules: {json.dumps(self.current_doc.modules, indent=2)}
        Current packages: {json.dumps(self.current_doc.packages, indent=2)}
        
        Provide feedback on:
        1. Alignment with Python best practices
        2. Potential issues (circular dependencies, coupling, cohesion)
        3. Suggested complementary components
        4. Implementation considerations
        5. Priority adjustment recommendation (current: {thought.priority}/5)
        
        Format response as structured JSON.
        """
        
        response = self.llm.complete(prompt, response_format="json")
        return response
    
    def refine_architecture(self) -> Dict[str, Any]:
        """Perform full architecture analysis and refinement."""
        prompt = f"""
        Analyze this complete architecture and provide comprehensive feedback:
        
        Project: {self.current_doc.project_name}
        Overview: {self.current_doc.overview}
        Modules: {json.dumps(self.current_doc.modules, indent=2)}
        Packages: {json.dumps(self.current_doc.packages, indent=2)}
        Dependencies: {json.dumps(self.current_doc.dependencies, indent=2)}
        
        Pending thoughts: {json.dumps([t.__dict__ for t in self.current_doc.thoughts if t.status == 'proposed'], indent=2)}
        
        Provide:
        1. Overall architecture assessment
        2. Suggested module additions/removals
        3. Package structure recommendations
        4. Dependency optimization suggestions
        5. Implementation priority order
        6. Potential risks and mitigations
        
        Return as JSON with keys: assessment, suggested_additions, suggested_removals, 
        package_recommendations, dependency_optimizations, priority_order, risks.
        """
        
        response = self.llm.complete(prompt, response_format="json")
        analysis = json.loads(response)
        
        # Save to history
        history_entry = {
            "timestamp": datetime.now().isoformat(),
            "version": self.current_doc.version,
            "analysis": analysis
        }
        self.current_doc.history.append(history_entry)
        
        return analysis
    
    def generate_mermaid_diagram(self) -> str:
        """Generate Mermaid diagram of current architecture."""
        prompt = f"""
        Generate a Mermaid diagram for this Python project architecture:
        
        Modules: {json.dumps(self.current_doc.modules, indent=2)}
        Packages: {json.dumps(self.current_doc.packages, indent=2)}
        Dependencies: {json.dumps(self.current_doc.dependencies, indent=2)}
        
        Create a classDiagram or flowchart showing:
        - All modules and their relationships
        - Package groupings
        - Dependency directions
        
        Output only valid Mermaid syntax.
        """
        
        return self.llm.complete(prompt)
    
    def finalize(self) -> Path:
        """Finalize architecture document and save to history."""
        self.current_doc.finalized_at = datetime.now()
        self.current_doc.version += 1
        
        # Save current version
        current_file = self.doc_path / "current" / "architecture.json"
        current_file.parent.mkdir(exist_ok=True)
        with open(current_file, 'w') as f:
            json.dump(self.current_doc.__dict__, f, indent=2, default=str)
        
        # Save to history
        history_file = self.history_path / f"v{self.current_doc.version}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(history_file, 'w') as f:
            json.dump(self.current_doc.__dict__, f, indent=2, default=str)
        
        # Generate Mermaid diagram
        mermaid = self.generate_mermaid_diagram()
        mermaid_file = self.doc_path / "diagrams" / f"architecture_v{self.current_doc.version}.mmd"
        mermaid_file.parent.mkdir(exist_ok=True)
        mermaid_file.write_text(mermaid)
        
        logger.info(f"Architecture document finalized: v{self.current_doc.version}")
        return current_file
    
    def interactive_session(self):
        """Run interactive architecture ideation session."""
        print("\n" + "="*60)
        print("Architecture Ideation Tool")
        print("="*60)
        
        project_name = input("Project name: ") or "document_engine"
        self.current_doc = self.load_or_create_document(project_name)
        
        while True:
            print(f"\n--- Architecture v{self.current_doc.version} ---")
            print(f"Thoughts: {len([t for t in self.current_doc.thoughts if t.status == 'proposed'])} pending")
            print(f"Modules: {len(self.current_doc.modules)}")
            print(f"Packages: {len(self.current_doc.packages)}")
            print("\nOptions:")
            print("1. Add architectural thought")
            print("2. View pending thoughts with AI feedback")
            print("3. Respond to AI feedback")
            print("4. Run full architecture refinement")
            print("5. Generate Mermaid diagram")
            print("6. View current architecture summary")
            print("7. Finalize and save")
            print("8. Exit")
            
            choice = input("\nSelect option: ").strip()
            
            if choice == '1':
                content = input("Describe your architectural thought: ")
                category = input("Category (module/package/interface/data_flow/dependency): ").strip()
                priority = int(input("Priority (1-5): ") or "3")
                thought = self.add_thought(content, category, priority)
                print(f"\n✓ Thought added (ID: {thought.id})")
                print(f"\nAI Feedback:\n{thought.ai_feedback}")
                
            elif choice == '2':
                pending = [t for t in self.current_doc.thoughts if t.status == 'proposed']
                for t in pending:
                    print(f"\n--- {t.id} (Priority: {t.priority}) ---")
                    print(f"Category: {t.category}")
                    print(f"Content: {t.content}")
                    print(f"AI Feedback: {t.ai_feedback}")
                    
            elif choice == '3':
                pending = [t for t in self.current_doc.thoughts if t.status == 'proposed']
                if not pending:
                    print("No pending thoughts.")
                    continue
                for i, t in enumerate(pending):
                    print(f"{i+1}. {t.id}: {t.content[:50]}...")
                idx = int(input("Select thought to respond: ")) - 1
                response = input("Your response to AI feedback: ")
                pending[idx].user_response = response
                pending[idx].status = input("Status (accepted/rejected): ").strip()
                
            elif choice == '4':
                print("Running full architecture analysis...")
                analysis = self.refine_architecture()
                print("\n=== AI Analysis ===")
                print(json.dumps(analysis, indent=2))
                
            elif choice == '5':
                mermaid = self.generate_mermaid_diagram()
                print("\n=== Mermaid Diagram ===\n")
                print(mermaid)
                
            elif choice == '6':
                print(f"\nProject: {self.current_doc.project_name}")
                print(f"Overview: {self.current_doc.overview or 'Not set'}")
                print("\nModules:")
                for m in self.current_doc.modules:
                    print(f"  - {m['name']}: {m.get('description', '')}")
                print("\nPackages:")
                for p in self.current_doc.packages:
                    print(f"  - {p['name']}: {len(p.get('modules', []))} modules")
                    
            elif choice == '7':
                self.finalize()
                print("Architecture document finalized and saved.")
                break
                
            elif choice == '8':
                break