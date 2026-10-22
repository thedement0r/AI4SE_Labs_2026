import argparse
import json
import sys
from pathlib import Path

from langgraph.graph import END, StateGraph

from state import AgentState
from nodes import (consolidator_agent_node, extractor_agent_node, load_docs_node,
                   model_names, render_document_node, validator_agent_node)


def routing_logic(state: AgentState):
    if state["stop_reason"] == "revise":
        print("[feedback] Issues found. Revising the previous draft.")
        return "go_to_consolidator"
    print(f"[stop] {state['stop_reason']}; approved={state['validation_passed']}")
    return "go_to_render"


def build_graph():
    workflow = StateGraph(AgentState)
    workflow.add_node("load_docs", load_docs_node)
    workflow.add_node("extractor_agent", extractor_agent_node)
    workflow.add_node("consolidator_agent", consolidator_agent_node)
    workflow.add_node("validator_agent", validator_agent_node)
    workflow.add_node("render_document", render_document_node)
    workflow.set_entry_point("load_docs")
    workflow.add_edge("load_docs", "extractor_agent")
    workflow.add_edge("extractor_agent", "consolidator_agent")
    workflow.add_edge("consolidator_agent", "validator_agent")
    workflow.add_conditional_edges("validator_agent", routing_logic, {
        "go_to_consolidator": "consolidator_agent", "go_to_render": "render_document",
    })
    workflow.add_edge("render_document", END)
    return workflow.compile()


def main(argv=None):
    parser = argparse.ArgumentParser(description="Refine source documents into an SRS.")
    parser.add_argument("input_dir", help="Directory containing ONLY corpus files")
    parser.add_argument("--output", default="output", help="Separate output directory")
    parser.add_argument("--max-rounds", type=int, default=3,
                        help="Total draft/review rounds, including the first (default: 3)")
    parser.add_argument("--exclude", action="append", default=[], help="Filename glob; repeatable")
    args = parser.parse_args(argv)
    
    if args.max_rounds < 1:
        parser.error("--max-rounds must be at least 1")

    if Path(args.input_dir).resolve() == Path(args.output).resolve():
        parser.error("Input and output directories must differ")
    names = model_names()

    if len(set(names.values())) != 3:
        parser.error("The assignment requires three different models (ANS4)")
    print(f"Models: {names}")

    try:
        result = build_graph().invoke({
            "input_dir": args.input_dir, "exclude_patterns": args.exclude,
            "max_rounds": args.max_rounds,
        }, config={"recursion_limit": 2 * args.max_rounds + 10})
    except Exception as exc:
        print(f"ERROR: {exc}\nNo new final document was saved.", file=sys.stderr)
        return 1
    
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    (output / "requirements_output.md").write_text(result["final_requirements_doc"], encoding="utf-8")
    (output / "run_details.json").write_text(json.dumps({
        "models": names,
        "source_files": [d["filename"] for d in result["raw_documents"]],
        "extracted_requirements": result["extracted_requirements"],
        "structured_document": result["structured_document"],
        "validation_history": result["validation_history"],
        "validation_passed": result["validation_passed"],
        "stop_reason": result["stop_reason"],
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Saved: {output / 'requirements_output.md'}")
    return 0 if result["validation_passed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
