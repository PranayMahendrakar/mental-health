"""
Mental Health Support Chatbot
Empathetic conversational AI for mental wellness support
Author: Pranay M

DISCLAIMER: This is not a replacement for professional mental health care.
If you're in crisis, please contact a mental health professional or crisis line.
"""

import ollama
import json
from datetime import datetime
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt
from rich.markdown import Markdown
import sys
import re

console = Console()
MODEL = "llama3.2"
DATA_DIR = Path("wellness_data")
DATA_DIR.mkdir(exist_ok=True)


# ============= System Prompts =============

EMPATHETIC_SYSTEM = """You are a compassionate mental wellness support companion. Your role is to:

1. Listen actively and empathetically without judgment
2. Validate emotions and experiences
3. Help users explore their thoughts and feelings
4. Suggest healthy coping strategies when appropriate
5. Encourage self-care and professional help when needed

IMPORTANT GUIDELINES:
- Never diagnose or provide medical/psychiatric advice
- If someone expresses thoughts of self-harm or suicide, gently encourage them to contact a crisis line or professional
- Focus on emotional support, not problem-solving unless asked
- Use reflective listening techniques
- Be warm, genuine, and non-judgmental
- Respect boundaries and don't push for details
- Acknowledge when something is beyond your scope

You are NOT a replacement for professional mental health care. Your purpose is to provide supportive conversation and wellness tools."""


# ============= Conversation Manager =============

class ConversationManager:
    """Manage empathetic conversations"""
    
    def __init__(self):
        self.history = []
        self.mood_log = []
        self.session_start = datetime.now()
    
    def add_message(self, role: str, content: str):
        """Add message to history"""
        self.history.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
    
    def get_response(self, user_message: str) -> str:
        """Get empathetic response"""
        self.add_message("user", user_message)
        
        # Check for crisis keywords
        if self._check_crisis(user_message):
            crisis_response = self._get_crisis_response()
            self.add_message("assistant", crisis_response)
            return crisis_response
        
        # Build conversation context
        messages = [{"role": "system", "content": EMPATHETIC_SYSTEM}]
        
        # Add recent history (last 10 exchanges)
        for msg in self.history[-20:]:
            messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })
        
        response = ollama.chat(model=MODEL, messages=messages)
        assistant_message = response['message']['content']
        
        self.add_message("assistant", assistant_message)
        return assistant_message
    
    def _check_crisis(self, message: str) -> bool:
        """Check for crisis indicators"""
        crisis_keywords = [
            "suicide", "kill myself", "end my life", "don't want to live",
            "want to die", "better off dead", "no reason to live",
            "self-harm", "hurt myself", "cutting myself"
        ]
        message_lower = message.lower()
        return any(keyword in message_lower for keyword in crisis_keywords)
    
    def _get_crisis_response(self) -> str:
        """Return crisis support message"""
        return """I hear that you're going through something really difficult right now, and I'm concerned about you. Your feelings are valid, and you deserve support.

🆘 **Please reach out to a crisis line:**
- **National Suicide Prevention Lifeline**: 988 (US)
- **Crisis Text Line**: Text HOME to 741741
- **International Association for Suicide Prevention**: https://www.iasp.info/resources/Crisis_Centres/

You don't have to face this alone. A trained counselor can provide the support you need right now.

I'm here to talk if you'd like, but please also consider reaching out to one of these resources. Would you like to tell me more about what's going on?"""
    
    def log_mood(self, mood: int, notes: str = ""):
        """Log mood entry (1-10 scale)"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "mood": mood,
            "notes": notes
        }
        self.mood_log.append(entry)
        return entry


# ============= Wellness Tools =============

class BreathingExercise:
    """Guided breathing exercises"""
    
    EXERCISES = {
        "box": {
            "name": "Box Breathing",
            "description": "A calming technique used by Navy SEALs",
            "steps": ["Inhale for 4 seconds", "Hold for 4 seconds", 
                     "Exhale for 4 seconds", "Hold for 4 seconds"],
            "cycles": 4
        },
        "478": {
            "name": "4-7-8 Breathing",
            "description": "A relaxation technique to reduce anxiety",
            "steps": ["Inhale through nose for 4 seconds",
                     "Hold breath for 7 seconds",
                     "Exhale through mouth for 8 seconds"],
            "cycles": 3
        },
        "calm": {
            "name": "Calming Breath",
            "description": "Simple deep breathing for quick calm",
            "steps": ["Take a slow, deep breath in",
                     "Feel your belly expand",
                     "Slowly exhale, releasing tension",
                     "Notice the calm spreading through you"],
            "cycles": 5
        }
    }
    
    def guide(self, exercise_type: str = "box") -> str:
        """Get breathing exercise guidance"""
        ex = self.EXERCISES.get(exercise_type, self.EXERCISES["box"])
        
        guide = f"""🌬️ **{ex['name']}**
{ex['description']}

Let's begin. Find a comfortable position and close your eyes if you'd like.

"""
        for cycle in range(1, ex['cycles'] + 1):
            guide += f"**Cycle {cycle}:**\n"
            for step in ex['steps']:
                guide += f"  • {step}\n"
            guide += "\n"
        
        guide += "Great job! Take a moment to notice how you feel."
        return guide


class GratitudeJournal:
    """Gratitude journaling tool"""
    
    def __init__(self):
        self.journal_file = DATA_DIR / "gratitude.json"
        self.entries = self._load()
    
    def _load(self) -> list:
        if self.journal_file.exists():
            return json.loads(self.journal_file.read_text())
        return []
    
    def _save(self):
        self.journal_file.write_text(json.dumps(self.entries, indent=2))
    
    def add_entry(self, items: list) -> dict:
        """Add gratitude entry"""
        entry = {
            "date": datetime.now().isoformat(),
            "items": items
        }
        self.entries.append(entry)
        self._save()
        return entry
    
    def get_prompt(self) -> str:
        """Get gratitude journaling prompt"""
        prompts = [
            "What made you smile today?",
            "Who are you grateful for in your life?",
            "What simple pleasure did you enjoy recently?",
            "What challenge taught you something valuable?",
            "What about your body are you grateful for?",
            "What's a small thing that made your day better?",
            "Who showed you kindness recently?"
        ]
        import random
        return random.choice(prompts)
    
    def get_recent(self, days: int = 7) -> list:
        """Get recent entries"""
        cutoff = datetime.now().timestamp() - (days * 86400)
        recent = []
        for entry in self.entries:
            entry_time = datetime.fromisoformat(entry['date']).timestamp()
            if entry_time >= cutoff:
                recent.append(entry)
        return recent


class MoodTracker:
    """Track mood over time"""
    
    def __init__(self):
        self.tracker_file = DATA_DIR / "mood_tracker.json"
        self.entries = self._load()
    
    def _load(self) -> list:
        if self.tracker_file.exists():
            return json.loads(self.tracker_file.read_text())
        return []
    
    def _save(self):
        self.tracker_file.write_text(json.dumps(self.entries, indent=2))
    
    def log(self, mood: int, feelings: list = None, notes: str = "") -> dict:
        """Log mood (1-10 scale)"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "mood": mood,
            "feelings": feelings or [],
            "notes": notes
        }
        self.entries.append(entry)
        self._save()
        return entry
    
    def get_summary(self, days: int = 7) -> dict:
        """Get mood summary"""
        cutoff = datetime.now().timestamp() - (days * 86400)
        recent = []
        
        for entry in self.entries:
            entry_time = datetime.fromisoformat(entry['timestamp']).timestamp()
            if entry_time >= cutoff:
                recent.append(entry)
        
        if not recent:
            return {"message": "No mood entries in this period"}
        
        moods = [e['mood'] for e in recent]
        avg_mood = sum(moods) / len(moods)
        
        all_feelings = []
        for e in recent:
            all_feelings.extend(e.get('feelings', []))
        
        feeling_counts = {}
        for f in all_feelings:
            feeling_counts[f] = feeling_counts.get(f, 0) + 1
        
        return {
            "entries": len(recent),
            "average_mood": round(avg_mood, 1),
            "highest": max(moods),
            "lowest": min(moods),
            "common_feelings": sorted(feeling_counts.items(), key=lambda x: -x[1])[:5]
        }


class Affirmations:
    """Positive affirmations generator"""
    
    AFFIRMATIONS = [
        "I am worthy of love and respect.",
        "I am doing the best I can, and that is enough.",
        "My feelings are valid and important.",
        "I choose to focus on what I can control.",
        "I am resilient and can handle challenges.",
        "I deserve to take care of myself.",
        "Today, I choose peace over anxiety.",
        "I am growing and learning every day.",
        "My past does not define my future.",
        "I am allowed to set boundaries.",
        "I am stronger than I think.",
        "I choose to be kind to myself today.",
        "My worth is not determined by my productivity.",
        "I am enough, exactly as I am.",
        "I give myself permission to rest."
    ]
    
    def get_affirmation(self) -> str:
        """Get random affirmation"""
        import random
        return random.choice(self.AFFIRMATIONS)
    
    def get_personalized(self, feeling: str) -> str:
        """Get AI-personalized affirmation"""
        prompt = f"""Create a warm, supportive affirmation for someone who is feeling {feeling}.

The affirmation should:
- Be in first person ("I am...")
- Be positive and empowering
- Be specific to their feeling
- Be believable and achievable

Just respond with the affirmation, nothing else."""

        response = ollama.generate(model=MODEL, prompt=prompt)
        return response['response'].strip()


class CopingStrategies:
    """Suggest coping strategies"""
    
    def get_strategy(self, situation: str) -> str:
        """Get coping strategy suggestion"""
        prompt = f"""Someone is dealing with: {situation}

Suggest 3-5 healthy coping strategies that could help. Include:
1. An immediate/short-term strategy
2. A mindfulness-based approach
3. A physical activity option
4. A social connection suggestion
5. A self-care activity

Be warm and supportive. Don't diagnose or give medical advice.
Keep suggestions practical and accessible."""

        response = ollama.generate(model=MODEL, prompt=prompt)
        return response['response']


# ============= CLI Interface =============

def show_banner():
    """Display application banner"""
    banner = """
╔══════════════════════════════════════════════════════════════╗
║           💚 Mental Wellness Companion 💚                     ║
║              Empathetic Support & Tools                       ║
║                   Author: Pranay M                            ║
╚══════════════════════════════════════════════════════════════╝
    """
    console.print(Panel(banner, style="bold green"))
    console.print("[dim]This is not a replacement for professional mental health care.[/dim]")
    console.print("[dim]In crisis? Call 988 (US) or text HOME to 741741[/dim]\n")


def show_menu():
    """Display main menu"""
    table = Table(title="Wellness Menu", show_header=False, box=None)
    table.add_column("Option", style="cyan")
    table.add_column("Description")
    
    table.add_row("1", "💬 Talk (Supportive Conversation)")
    table.add_row("2", "🌬️  Breathing Exercises")
    table.add_row("3", "📊 Log Mood")
    table.add_row("4", "🙏 Gratitude Journal")
    table.add_row("5", "✨ Get Affirmation")
    table.add_row("6", "🛠️  Coping Strategies")
    table.add_row("7", "📈 View Mood Summary")
    table.add_row("0", "🚪 Exit")
    
    console.print(table)


def talk_session():
    """Start supportive conversation"""
    console.print("\n[green]I'm here to listen. Share what's on your mind.[/green]")
    console.print("[dim]Type 'done' when you're ready to end the conversation.[/dim]\n")
    
    conversation = ConversationManager()
    
    while True:
        user_input = Prompt.ask("[cyan]You[/cyan]")
        
        if user_input.lower() in ['done', 'exit', 'quit', 'bye']:
            console.print("\n[green]Thank you for sharing with me today. Take care of yourself. 💚[/green]")
            break
        
        response = conversation.get_response(user_input)
        console.print(f"\n[green]Companion:[/green] {response}\n")


def breathing_exercise():
    """Guide through breathing exercise"""
    breathing = BreathingExercise()
    
    console.print("\n[cyan]Choose a breathing exercise:[/cyan]")
    console.print("1. Box Breathing (calming)")
    console.print("2. 4-7-8 Breathing (anxiety relief)")
    console.print("3. Calming Breath (quick calm)")
    
    choice = Prompt.ask("Select", default="1")
    
    exercise_map = {"1": "box", "2": "478", "3": "calm"}
    exercise_type = exercise_map.get(choice, "box")
    
    guide = breathing.guide(exercise_type)
    console.print(Panel(guide, border_style="blue"))


def log_mood():
    """Log current mood"""
    tracker = MoodTracker()
    
    console.print("\n[cyan]How are you feeling right now?[/cyan]")
    console.print("Rate your mood from 1 (very low) to 10 (excellent)")
    
    mood = Prompt.ask("Mood (1-10)", default="5")
    try:
        mood = max(1, min(10, int(mood)))
    except:
        mood = 5
    
    feelings_list = ["anxious", "sad", "stressed", "tired", "calm", "happy", 
                     "grateful", "frustrated", "hopeful", "lonely"]
    
    console.print("\n[cyan]Select any feelings that apply (comma-separated numbers):[/cyan]")
    for i, f in enumerate(feelings_list, 1):
        console.print(f"  {i}. {f}")
    
    selected = Prompt.ask("Feelings", default="")
    feelings = []
    if selected:
        for num in selected.split(","):
            try:
                idx = int(num.strip()) - 1
                if 0 <= idx < len(feelings_list):
                    feelings.append(feelings_list[idx])
            except:
                pass
    
    notes = Prompt.ask("Any notes? (optional)", default="")
    
    entry = tracker.log(mood, feelings, notes)
    
    console.print(f"\n[green]Mood logged: {mood}/10[/green]")
    if feelings:
        console.print(f"Feelings: {', '.join(feelings)}")
    
    # AI response to mood
    if mood <= 3:
        console.print("\n[yellow]I notice you're having a tough time. Would you like to talk about it?[/yellow]")
    elif mood >= 8:
        console.print("\n[green]Wonderful! It's great you're feeling good today! 🌟[/green]")


def gratitude_journal():
    """Gratitude journaling"""
    journal = GratitudeJournal()
    
    console.print("\n[cyan]🙏 Gratitude Journal[/cyan]")
    prompt = journal.get_prompt()
    console.print(f"\n[yellow]Prompt: {prompt}[/yellow]\n")
    
    console.print("Enter 3 things you're grateful for (one per line):")
    items = []
    for i in range(3):
        item = Prompt.ask(f"  {i+1}")
        if item:
            items.append(item)
    
    if items:
        journal.add_entry(items)
        console.print("\n[green]Your gratitude has been recorded. Thank you for reflecting! 🙏[/green]")


def get_affirmation():
    """Get positive affirmation"""
    affirmations = Affirmations()
    
    console.print("\n[cyan]Would you like:[/cyan]")
    console.print("1. A random affirmation")
    console.print("2. A personalized affirmation")
    
    choice = Prompt.ask("Select", default="1")
    
    if choice == "2":
        feeling = Prompt.ask("How are you feeling right now?")
        affirmation = affirmations.get_personalized(feeling)
    else:
        affirmation = affirmations.get_affirmation()
    
    console.print(Panel(f"✨ {affirmation} ✨", border_style="magenta"))


def coping_strategies():
    """Get coping strategy suggestions"""
    coping = CopingStrategies()
    
    situation = Prompt.ask("\n[cyan]What are you dealing with?[/cyan]")
    
    console.print("\n[dim]Finding helpful strategies...[/dim]\n")
    strategies = coping.get_strategy(situation)
    
    console.print(Panel(strategies, title="Coping Strategies", border_style="cyan"))


def view_mood_summary():
    """View mood tracking summary"""
    tracker = MoodTracker()
    
    days = Prompt.ask("Days to summarize", default="7")
    try:
        days = int(days)
    except:
        days = 7
    
    summary = tracker.get_summary(days)
    
    if 'message' in summary:
        console.print(f"[yellow]{summary['message']}[/yellow]")
        return
    
    table = Table(title=f"Mood Summary (Last {days} Days)")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    
    table.add_row("Entries", str(summary['entries']))
    table.add_row("Average Mood", f"{summary['average_mood']}/10")
    table.add_row("Highest", f"{summary['highest']}/10")
    table.add_row("Lowest", f"{summary['lowest']}/10")
    
    if summary['common_feelings']:
        feelings = ", ".join([f"{f[0]} ({f[1]})" for f in summary['common_feelings']])
        table.add_row("Common Feelings", feelings)
    
    console.print(table)


def main():
    """Main entry point"""
    show_banner()
    
    # Check Ollama
    try:
        ollama.list()
    except Exception:
        console.print("[red]Error: Ollama not running. Start with: ollama serve[/red]")
        sys.exit(1)
    
    while True:
        show_menu()
        choice = Prompt.ask("\nWhat would you like to do?", default="0")
        
        if choice == "0":
            console.print("\n[green]Take care of yourself. You matter. 💚[/green]")
            break
        elif choice == "1":
            talk_session()
        elif choice == "2":
            breathing_exercise()
        elif choice == "3":
            log_mood()
        elif choice == "4":
            gratitude_journal()
        elif choice == "5":
            get_affirmation()
        elif choice == "6":
            coping_strategies()
        elif choice == "7":
            view_mood_summary()
        else:
            console.print("[red]Invalid option[/red]")
        
        console.print("\n" + "="*60 + "\n")


if __name__ == "__main__":
    main()
