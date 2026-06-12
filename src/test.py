import syncedlyrics

lyrics = syncedlyrics.search("Lover Taylor Swift")
if lyrics:
    print("✅ Works!")
    print(lyrics[:200])
else:
    print("Not found")