from typing import Dict, Any, Optional, List
import json
import structlog
from datetime import datetime

from app.settings import config

logger = structlog.get_logger()


class FlowEngine:
    def __init__(self):
        self.active_sessions = {}  # user_id -> session_data
        self.flows = config.get("flows", {})
    
    def start_flow(self, flow_name: str, user_id: str, channel: str) -> Dict[str, Any]:
        """Start a new flow for a user"""
        if flow_name not in self.flows:
            return {"error": f"Flow '{flow_name}' not found"}
        
        flow = self.flows[flow_name]
        session = {
            "flow_name": flow_name,
            "user_id": user_id,
            "channel": channel,
            "current_step": 0,
            "variables": {},
            "started_at": datetime.utcnow().isoformat(),
            "completed": False
        }
        
        self.active_sessions[user_id] = session
        
        # Return first step
        return self._get_current_step_response(session)
    
    def process_message(self, user_id: str, message: str) -> Dict[str, Any]:
        """Process user message in an active flow"""
        if user_id not in self.active_sessions:
            return {"error": "No active flow"}
        
        session = self.active_sessions[user_id]
        if session["completed"]:
            return {"error": "Flow already completed"}
        
        flow = self.flows[session["flow_name"]]
        steps = flow.get("steps", [])
        current_step_idx = session["current_step"]
        
        if current_step_idx >= len(steps):
            return {"error": "Flow completed"}
        
        current_step = steps[current_step_idx]
        
        # Validate and store the user input
        validation_result = self._validate_input(message, current_step)
        if not validation_result["valid"]:
            return {
                "text": validation_result["error"],
                "flow_active": True,
                "step": current_step_idx
            }
        
        # Store the variable
        var_name = current_step.get("var")
        if var_name:
            session["variables"][var_name] = validation_result["value"]
        
        # Move to next step
        session["current_step"] += 1
        
        # Check if flow is complete
        if session["current_step"] >= len(steps):
            return self._complete_flow(session)
        
        # Return next step
        return self._get_current_step_response(session)
    
    def _validate_input(self, input_text: str, step: Dict[str, Any]) -> Dict[str, Any]:
        """Validate user input based on step requirements"""
        validation = step.get("validation", "")
        value = input_text.strip()
        
        if validation == "required" and not value:
            return {"valid": False, "error": "Este campo es requerido."}
        
        elif validation == "number":
            try:
                value = int(value)
                if value <= 0:
                    return {"valid": False, "error": "Debe ser un número mayor a 0."}
            except ValueError:
                return {"valid": False, "error": "Debe ser un número válido."}
        
        elif validation == "phone":
            # Simple phone validation
            import re
            phone_pattern = r'^[\+]?[\d\s\-\(\)]{8,15}$'
            if not re.match(phone_pattern, value):
                return {"valid": False, "error": "Ingresa un teléfono válido."}
        
        elif validation == "email":
            import re
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, value):
                return {"valid": False, "error": "Ingresa un email válido."}
        
        return {"valid": True, "value": value}
    
    def _get_current_step_response(self, session: Dict[str, Any]) -> Dict[str, Any]:
        """Get response for current step"""
        flow = self.flows[session["flow_name"]]
        steps = flow.get("steps", [])
        current_step = steps[session["current_step"]]
        
        # Format the question with existing variables
        question = current_step.get("ask", current_step.get("confirm", ""))
        formatted_question = self._format_template(question, session["variables"])
        
        response = {
            "text": formatted_question,
            "flow_active": True,
            "flow_name": session["flow_name"],
            "step": session["current_step"],
            "total_steps": len(steps)
        }
        
        # Add quick replies if this is a product selection step
        if current_step.get("var") == "product":
            response["quick_replies"] = ["Pizza", "Hamburguesa", "Tacos", "Ver menú completo"]
        
        return response
    
    def _complete_flow(self, session: Dict[str, Any]) -> Dict[str, Any]:
        """Complete the flow and perform final actions"""
        session["completed"] = True
        session["completed_at"] = datetime.utcnow().isoformat()
        
        flow_name = session["flow_name"]
        variables = session["variables"]
        
        if flow_name == "quick_order":
            # Create order record
            order_data = {
                "customer_name": variables.get("name", ""),
                "phone": variables.get("phone", ""),
                "product": variables.get("product", ""),
                "quantity": variables.get("qty", 1),
                "channel": session["channel"]
            }
            
            # This would normally save to database
            logger.info(f"Order created: {order_data}")
            
            business_name = config.get("business", {}).get("name", "nuestro negocio")
            confirmation_text = f"¡Perfecto! Tu pedido ha sido recibido. El equipo de {business_name} te contactará pronto al {variables.get('phone')} para confirmar los detalles."
            
            # Clean up session
            del self.active_sessions[session["user_id"]]
            
            return {
                "text": confirmation_text,
                "flow_active": False,
                "flow_completed": True,
                "order_data": order_data
            }
        
        return {
            "text": "Flujo completado.",
            "flow_active": False,
            "flow_completed": True
        }
    
    def _format_template(self, template: str, variables: Dict[str, Any]) -> str:
        """Format template string with variables"""
        try:
            return template.format(**variables)
        except KeyError as e:
            logger.warning(f"Missing variable in template: {e}")
            return template
    
    def cancel_flow(self, user_id: str) -> bool:
        """Cancel active flow for user"""
        if user_id in self.active_sessions:
            del self.active_sessions[user_id]
            return True
        return False
    
    def get_active_flow(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get active flow session for user"""
        return self.active_sessions.get(user_id)
    
    def is_flow_active(self, user_id: str) -> bool:
        """Check if user has an active flow"""
        return user_id in self.active_sessions and not self.active_sessions[user_id]["completed"]


# Global flow engine instance
flow_engine = FlowEngine()