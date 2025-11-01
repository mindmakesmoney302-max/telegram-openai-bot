user_histories = {}
MAX_HISTORY = 10

def add_message(user_id: int, role: str, content: str):
    if user_id not in user_histories:
        user_histories[user_id] = []
    user_histories[user_id].append({"role": role, "content": content})
    user_histories[user_id] = user_histories[user_id][-MAX_HISTORY:]

def get_history(user_id: int):
    return user_histories.get(user_id, [])

def clear_history(user_id: int):
    user_histories[user_id] = []
