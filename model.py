from dataclasses import dataclass
from datetime import datetime

@dataclass
class User:
    id: int
    username: str
    created_at: datetime

@dataclass
class Account:
    id: int
    user_id: int
    name: str
    type: str
    balance: float
    created_at: datetime

@dataclass
class Category:
    id: int
    user_id: int
    name: str
    type: str

@dataclass
class Transaction:
    id: int
    user_id: int
    account_id: int
    type: str
    amount: float
    category_id: int
    date: datetime
    description: str
    created_at: datetime