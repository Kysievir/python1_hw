outcomes = list(input())

alice_wins = outcomes.count("A")
bob_wins = outcomes.count("B")

if alice_wins > bob_wins:
    print("ALICE")
elif alice_wins < bob_wins:
    print("BOB")
else:
    print("DRAW")