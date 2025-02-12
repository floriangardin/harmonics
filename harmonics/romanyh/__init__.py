
from .voicing import solveProgressionChords, generateHarmonization

def generateBestHarmonization(chords,
    closePosition=False,
    firstVoicing=None,
    lastVoicing=None,
    allowedUnisons=0):

    costTable = solveProgressionChords(chords, 
                                       closePosition=closePosition, 
                                       firstVoicing=firstVoicing, 
                                       lastVoicing=lastVoicing, 
                                       allowedUnisons=allowedUnisons)
    progression, cost = next(generateHarmonization(costTable))
    return progression