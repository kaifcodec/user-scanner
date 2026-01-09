from user_scanner.core import helpers
from types import SimpleNamespace

def test_generate_permutations():
    perms = helpers.generate_permutations("user", "ab", limit=None)    
    assert "user" in perms  
    # All permutations must be valid
    assert all(
        p == "user" or
        (p.startswith("user") and len(p) > len("user"))
        for p in perms
    )
    
    assert len(perms) > 1

def test_generate_permutations_email():
    perms = helpers.generate_permutations("john@email.com", "abc", limit=None, is_email=True)    
    assert "john@email.com" in perms  
    assert all(
        p == "john@email.com" or
        (p.startswith("john") and len(p) > len("john@email.com") and p.endswith("@email.com"))
        for p in perms
    )
    assert len(perms) > 1

def test_get_site_name():
    def module(name:str) -> SimpleNamespace:
        return SimpleNamespace(**{"__name__":name})
    assert helpers.get_site_name(module("X")) == "X (Twitter)"
    assert helpers.get_site_name(module("x")) == "X (Twitter)"
    assert helpers.get_site_name(module("user_scanner.github")) == "Github"
    assert helpers.get_site_name(module("user_scanner.chess_com")) == "Chess.com"
    

