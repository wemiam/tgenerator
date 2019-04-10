def more_similiar(keywords, input, inputword , leftDict , currentDict):
    wordsSimilar = input[inputword]

    sameLevelNodes=[]
    subLevelNodes = []


    for eachTag in keywords:
        for wordSimilar in wordsSimilar['similarities']:
            if wordSimilar[0] == eachTag:
                break


        # sub level of input word
        if not wordSimilar[1] == 'unknown' and wordSimilar[1] > 0.25 and leftDict.count(wordSimilar[0]) > 0:
            #    print(wordSimilar[0])
            currentDict[inputword].update({wordSimilar[0]: {}})
            leftDict.remove(wordSimilar[0])
            subLevelNodes.append(wordSimilar[0])

    for sameLevelNode in sameLevelNodes:
        #print('samenode' + sameLevelNode)
        if sameLevelNode == '成本':
            print()
        more_similiar(keywords, input, sameLevelNode, leftDict, currentDict)

    for subLevelNode in subLevelNodes:
        more_similiar(keywords, input, subLevelNode, leftDict, currentDict[inputword])

def get_taxonomy_old(keywords, input):
    loclist = []
    perlist = []
    orglist = []
    unknownlist = []
    leftDict = []

    result = {'location': {}, 'person': {}, 'org': {}, 'other': {}}

    #get first level, each type get the No1 tag as root
    for i in range(len(keywords)):

        tag = keywords[i]
        if input[tag]['entity'] == 'LOC' and len(loclist) == 0:
            loclist.append(tag)
            result['location'].update({tag: {}})
        elif input[tag]['entity'] == 'PER' and len(perlist) == 0:
            perlist.append(tag)
            result['person'].update({tag: {}})
        elif input[tag]['entity'] == 'ORG' and len(orglist) == 0:
            orglist.append(tag)
            result['org'].update({tag: {}})
        elif input[tag]['entity'] == 'UNKNOWN' and len(input[tag]['similarities']) > 0 and len(unknownlist) == 0:
            unknownlist.append(tag)
        else:
            leftDict.append(tag)


    for loc in loclist:
        more_similiar(keywords, input, loc, leftDict, result['location'])

    for per in perlist:
        more_similiar(keywords, input, per, leftDict, result['person'])

    for org in orglist:
        more_similiar(keywords, input, org, leftDict, result['org'])

    # handle all the left words

    print("left : " + str(leftDict))

    for word in leftDict:
        result['other'].update({word: {}})
        leftDict.remove(word)
        more_similiar(keywords, input, word, leftDict, result['other'])

    return result


def get_taxonomy(keywords, input):
    loclist = []
    result = {'location': {}, 'person': {}, 'org': {}, 'other': {}}

    leftDict = list(keywords).copy()

    #get first level, get 10% of the nodes
    for i in range(len(keywords)//10):
        tag = keywords[i]
        if leftDict.count(tag) > 0:
            wordsSimilar = input[tag]
            print(tag)
            loclist.append(tag)
            result['location'].update({tag: {}})
            leftDict.remove(tag)

        # if root node similar, put together
        for j in range(i, len(keywords)//10):
            if leftDict.count(keywords[j]) > 0:
                for wordSimilar in wordsSimilar['similarities']:
                    if wordSimilar[0] == keywords[j]:
                        print(wordSimilar[1])
                        if wordSimilar[1] == 'unknown':
                            print()
                        elif wordSimilar[1] > 0.25:
                            result['location'][tag].update({keywords[j]: {}})
                            leftDict.remove(keywords[j])

    for loc in loclist:
        more_similiar(keywords, input, loc, leftDict, result['location'])

    # handle all the left words
    for word in leftDict:
        result['other'].update({word: {}})
        leftDict.remove(word)
        more_similiar(keywords, input, word, leftDict, result['other'])


    #remove single nodes
    for key in list(result['other'].keys()):
        print(len(result['other'][key]))
        print(result['other'][key])
        if len(result['other'][key]) == 0:
            result['other'].pop(key)

    return result