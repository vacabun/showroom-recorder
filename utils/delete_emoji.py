import argparse
import re
import emoji #仅用于YouTube可以删除
import os

#emojis to be kept as symbols
#可转换为字符的emoji ：“http://unicode.org/emoji/charts/emoji-variants.html”
a = ["☝","♥","✌","❤","♀","♂","❣"]
b = [":index_pointing_up:",":heart_suit:",":victory_hand:",":red_heart:",":female_sign:",":male_sign:",":heart_exclamation:"]
dict1=dict(zip(b,a))

#font for Unicode Blocks {“大致分类”：“字体”}
dict2={'Arabic':'Geeza Pro',
'Latin1Supplement':'Lucida Grande',
'LatinExtendedAB':'Microsoft Sans Serif',
'GreekandCoptic':'Lucida Grande',
'Cyrillic':'Microsoft Sans Serif',
'Armenian':'Mshtakan',
'IPAExtensions':'Lucida Grande',
'PhoneticExtensions':'Microsoft Sans Serif',
'Devanagar':'Kohinoor Devanagari',
'Gurmukhi':'Mukta Mahee',
'Oriya':'Oriya',
'Tamil':'Tamil MN',
'Kannada':'Noto Sans Kannada',
'Tibetan':'Kailasa',
'Thai':'Thonburi',
'UnifiedCanadianAboriginalSyllabics':'Euphemia UCAS',
'HangulJamo':'Arial Unicode MS',
'Hangul':'Apple SD Gothic Neo',
'KatakanaPhoneticExtensions':'Hiragino Sans',
'Halfwidthkatakana':'Hiragino Sans',
'HalfwidthHangul':'Arial Unicode MS',
'Bopomofo':'Arial Unicode MS',
'Yi':'STHeiti',
'SpacingModifierLetters':'Microsoft Sans Serif',
'SuperscriptsandSubscripts':'Menlo',
'CombiningDiacriticalMarks':'Microsoft Sans Serif',
'CombiningDiacriticalMarksSupplement':'Geneva',
'CombiningDiacriticalMarksforSymbols':'STIXGeneral',
'CJKCompatibilityForms':'Hiragino Sans GB',
'LetterlikeSymbols':'Arial Unicode MS',
'MathematicalAlphanumericSymbols':'STIXGeneral',
'CJKCompatibility':'MS PGothic',
'BoxDrawing':'MS PGothic',
'MiscellaneousTechnical':'Apple Symbols',
'NKo':'NotoSansNKo-Regular',
'Lao':'Arial Unicode MS',
'Malayalam':'Malayalam MN',
'GeometricShapes':'Apple Symbols',
'Batak':'NotoSansBatak-Regular',   #could be selected as fallback
'Hebrew':'Microsoft Sans Serif',
'Bengali':'Kohinoor Bangla',
'Gujarati':'Kohinoor Gujarati',
'Telugu':'Kohinoor Telugu',
'Sinhala':'Sinhala MN',
'Georgian':'Arial Unicode MS',
'Cherokee':'Galvji',
'Mongolian':'STHeiti',
'OpticalCharacterRecognition':'Arial Unicode MS',
'Arrows':'Apple Symbols',
'EnclosedAlphabet':'Arial Unicode MS',
'unicodeinhelvetica':'Helvetica',
'CJKinkaomoji':'Hiragino Sans',
'kaomojibetterinhiragino':'Hiragino Sans',
'kaomojibetterinMSPGothic':'MS PGothic',
'kaomojibetterinArialUnicodeMS':'Arial Unicode MS',
'kaomojibetterinmeiryo':'meiryo',
'kaomojibetterinAppleSymbols':'Apple Symbols',
'emojikeptassymbols':'MS PGothic', #如有添加保留为符号的emoji记得确认MSPGothic能否显示
#'Phoenician':'Aegean'
}

def delete_emoji(inputfile):
        
    #input
    with open(inputfile,'r',encoding='UTF-8') as f1:
        content = f1.read()
    content=emoji.demojize(content) #仅用于YouTube可以删除
    #keep symbols
    for search,replace in dict1.items():
        content =  content.replace(search,replace)
    #delete emojis
    content = re.sub ('(\:[ÅA-za-z]+.*?\:|\:[0-9][A-za-z]+\:|\:[0-9]{3,4}\:|\:[+-]1\:)','',content)
    #set  <font name> specifies for kaomojis in ass
    def fnfont(input,language):
        input2 = '{\\fn'+dict2[language]+'}'+input+'{\\r}'
        return input2

    #compile unicode blocks
    Arabic = re.compile('[\u0600-\u06ff\u0750-\u077f\u08a0-\u08ff\ufeff|ﻌ]') #\ufeff:ZERO WIDTH NO-BREAK SPACE
    Latin1Supplement=re.compile('[\u0080-\u00ff|ↀↁↂ]')
    LatinExtendedAB=re.compile('[\u0100-\u017f\u0180-\u024f]')
    GreekandCoptic=re.compile('[\u0374\u0375\u037a-\u037e\u0384-\u03ce\u03d0-\u03ff\u03ff\u1f00-\u1fff]') #\u1f00-\u1fff:Greek Extended #GreekandCoptic Except:"ͰͱͲͳͶͷͿϏ"
    Cyrillic=re.compile('[\u0400-\u0486\u0488-\u04ff\u0500-\u0513]') #except \u0487:"◌҇" #\u0500-\u0513:Cyrillic Supplement except \u0514-\u052f
    Armenian=re.compile('[\u0530-\u058a]') #except \u058d-\u058f:"֍֎֏"
    IPAExtensions=re.compile('[\u0250-\u02af\u20e3]') #\u20e3:COMBINING ENCLOSING KEYCAP
    PhoneticExtensions=re.compile('[\u1d00-\u1d7f\u1d80-\u1dbf]') #\u1d80-\u1dbf Phonetic Extensions Supplement
    Devanagar=re.compile('[\u0900-\u097f]')
    Gurmukhi=re.compile('[\u0a00-\u0a75|₹]') #except \u0a76:"੶"
    Oriya=re.compile('[\u0b00-\u0b54\u0b56-\u0b7f]') #except \u0b55:"୕"
    Tamil=re.compile('[\u0b80-\u0bff]')
    Kannada=re.compile('[\u0c80-\u0c83\u0c85-\u0cd6\u0cde-\u0cff]') #except \u0c84\u0cdd
    Tibetan=re.compile('[\u0f00-\u0f8b\u0f90-\u0fd8]') #except \u0f8c-\u0f8f\u0fd9-\u0fda
    Thai=re.compile('[\u0e00-\u0e7f]')
    UnifiedCanadianAboriginalSyllabics=re.compile('[\u1401-\u1676]') #except \u1400:"᐀" \u1677-\u167f:"ᙷᙸᙹᙺᙻᙼᙽᙾᙿ"
    HangulJamo=re.compile('[\u1100-\u1159\u1155-\u11a2\u11a8-\u11f9\u20d0-\u20e1]') #except \u115a-\u115e \u11a3-\u11a7 \u11fa-\u11ff　#\u20d0-\u20e1:combining symbols
    Hangul=re.compile('[\u3130-\u318f\uac00-\ud7a3]')
    KatakanaPhoneticExtensions=re.compile('[\u31f0-\u31ff]')
    Halfwidthkatakana=re.compile('[\uff5f-\uff9f]')
    HalfwidthHangul=re.compile('[\uffa0-\uffef]')
    Bopomofo=re.compile('[\u3100-\u312c]') #except:\u312d-\u312f:"ㄭㄮㄯ"
    Yi=re.compile('[\ua000-\ua48f\ua490-\ua4a1\ua4a4-\ua4b3\ua4b5-\ua4c0\ua4c2-\ua4c4\ua4c6]')
    #\ua000-\ua48f:Yi Syllables #\ua490-\ua4cf:Yi Radicals except:\ua4a2-\ua4a3\ua4b4\ua4c1\ua4c5:"꒢꒣꒴꓁꓅"
    SpacingModifierLetters=re.compile('[\u02b0-\u02ff]')
    SuperscriptsandSubscripts=re.compile('[\u2070-\u2094]') #except \u2095-\u209c:"ₕₖₗₘₙₚₛₜ"
    CombiningDiacriticalMarks=re.compile('[\u0300-\u036f\ufb1d-\ufb4f]') #\ufb1d-\ufb4f:Alphabetic Presentation Forms else in kaomojibetterinArialUnicodeMS
    CombiningDiacriticalMarksSupplement=re.compile('[\u1dc0-\u1dcf\u1dd3-\u1dd9\u1ddb-\u1de6\u1dfe-\u1dff|Ↄↄↅↆ|\ua700-\ua71f]')
    #except \u1dd0-\u1dd2\u1dda\u1de7-\u1dfd #\ua700-\ua71f:Modifier Tone Letters
    CombiningDiacriticalMarksforSymbols=re.compile('[\u20e4-\u20ff\u213c-\u214b]')  #except \u20e2 #else in HangulJamo:Arial Unicode MS and IPAExtensions:Lucida Grande
    CJKCompatibilityForms=re.compile('[\ufe30-\ufe31\ufe33-\ufe44\ufe49-\ufe4f|﹡]') #\ufe31:'︲'in Yi:STHeiti #\ufe45-\ufe48:"﹅﹆﹇﹈" in kaomojibetterinhiragino:Hiragino Sans
    LetterlikeSymbols=re.compile('[\u2100-\u2138]') #except \u214c\u214f:"⅌⅏"
    #\u2139-\u213b\u214d-\u214e in MiscellaneousTechnical:Applesymbols #\u213c-\u214b in CombiningDiacriticalMarksforSymbols':'STIXGeneral'
    MathematicalAlphanumericSymbols=re.compile('[\u2139-\u213b\u214d-\u214e\U0001D400-\U0001D7C9\U0001D7CE-\U0001D7FF]')#except \U0001D7CA-\U0001D7CB:"𝟊𝟋"
    CJKCompatibility=re.compile('[\u3300-\u3376\u337b-\u33dd\u33e0-\u33fe]') #except \u3377-\u337a\u33de-\u33df\u33ff:"㍷㍸㍹㍺㏞㏟㏿"
    BoxDrawing=re.compile('[\u2500-\u257f]')
    MiscellaneousTechnical=re.compile('[\u2300-\u23e7]') #except \u23e8-\u23ff
    NKo=re.compile('[\u07c0-\u07fa]') #except \u07fd-\u07ff
    Lao=re.compile('[\u0e80-\u0e84\u0e87-\u0e88\u0e8a\u0e8d\u0e94-\u0e97\u0e99-\u0e9f\u0ea1-\u0ea7\u0eaa-\u0eab\u0ead-\u0eb9\u0ebb-\u0edd]')
    #except \u0e86\u0e89\u0e8c\u0e8e-\u0e93\u0e98\u0ea0\u0ea8-\u0ea9\u0eac\u0eba\u0ede-\u0edf
    Malayalam=re.compile('[\u0d01-\u0d03\u0d05-\u0d3a\u0d3d-\u0d4e\u0d57\u0d5f-\u0d75\u0d79-\u0d7f]')
    #except \u0d00\u0d04\u0d3b-\u0d3c\u0d4f-\u0d56\u0d58-u0d5e\u0d76-\u0d78
    GeometricShapes=re.compile('[\u25a0-\u25ff\u2200-\u22ff]') #\u2200-\u22ff:Mathematical Operators (Unicode block)
    Batak=re.compile('[\u1bc0-\u1bff]')  #could be selected as fallback
    Hebrew=re.compile('[\u0590-\u05ea\u05f0-\u05f4]') #except \u05ef
    Bengali=re.compile('[\u0980-\u09fb]') #except \u09fc-\u09fe
    Gujarati=re.compile('[\u0a80-\u0af9]') #except \u0afa-\u0aff
    Telugu=re.compile('[\u0c00-\u0c03\u0c05-\u0c39\u0c3d-\u0c5a\u0c60-\u0c6f\u0c78-\u0c7f]') #except \u0c04\u0c3c\u0c5d\u0c77
    Sinhala=re.compile('[\u0d81-\u0ddf\u0df2-\u0df4]')#except \u0d81\u0de6-\u0def
    Georgian=re.compile('[\u10a0-\u10c5\u10d0-\u10f6\u10fb]')#except \u10c7\u10cd #else \u10f7-\u10fa\u10fc-\u10ff in unicodeinhelvetica
    Cherokee=re.compile('[\u13a0-\u13ff]')
    Mongolian=re.compile('[\u1800-\u1877\u1880-\u18a9]')#except \u1878\u18aa
    OpticalCharacterRecognition=re.compile('[\u2440-\u244a]')
    Arrows=re.compile('[\u2190-\u21ff\u2580-\u259f]') #\u2580-\u259f:Block Elements
    EnclosedAlphabet=re.compile('[\u24b6-\u24e9\u3260-\u327b\u32d0-\u32fe]')#\u3260-\u327b:Enclosed Hangul \u32d0-\32fe:Enclosed Katakana
    unicodeinhelvetica=re.compile('[\u10f7-\u10fa\u10fc-\u10ff|Ⱡⱶ|⸅⸌|⸜⸝]')
    CJKinkaomoji="乂卍彡艸灬罒"
    kaomojibetterinhiragino="Ⅲ⦿﹅﹆﹇﹈"
    kaomojibetterinMSPGothic="‧‸‿☝☆★♡♥♪♬✧✾❁❛❜✕✘✟✩✪✰✹✺✽✿❀❆❍❝❥❦➲"
    kaomojibetterinArialUnicodeMS=re.compile('[\ufb00-\ufb17\ufe20-\ufe23|�]')
    kaomojibetterinmeiryo="⺫"
    kaomojibetterinAppleSymbols="☉☌☓☚☛☜☞☫☻☼♛♜♤♧♩♫♯⚈⚨⚬⚲"
    #如果新增的dict1内容需要两种以上的字体才能显示，对下行以及compile进行细分类
    emojikeptassymbols=''.join(a)
    #Phoenician=re.compile('[\U00010900-\U0001091F]')
    #Phoenician="𐤔𐤀𐤕𐤖𐤗𐤘𐤙𐤚𐤛𐤂𐤁𐤄𐤅𐤆𐤇𐤈𐤉𐤊𐤋𐤌𐤍𐤎𐤏𐤐𐤑𐤒𐤓𐤔"
    #腓尼基字母由于一般会被自动替换为异体字显示 用Aegean字体虽然能让它不乱码但作为颜文字显示效果不好 故直接把"𐤔"替换为"w"
    #210908 "ゔ"在苹方中不显示，因制作日语弹幕时一般会选择非苹方的日语字体故不考虑

    contentlst=set(list(content))
    content2=''.join(contentlst)
    for it in content2:
        if Arabic.search(it):
            content=content.replace(it,fnfont(it,'Arabic'))
        elif Latin1Supplement.search(it):
            content=content.replace(it,fnfont(it,'Latin1Supplement'))
        elif LatinExtendedAB.search(it):
            content=content.replace(it,fnfont(it,'LatinExtendedAB'))
        elif GreekandCoptic.search(it):
            content=content.replace(it,fnfont(it,'GreekandCoptic'))
        elif Cyrillic.search(it):
            content=content.replace(it,fnfont(it,'Cyrillic'))
        elif Armenian.search(it):
            content=content.replace(it,fnfont(it,'Armenian'))
        elif IPAExtensions.search(it):
            content=content.replace(it,fnfont(it,'IPAExtensions'))
        elif PhoneticExtensions.search(it):
            content=content.replace(it,fnfont(it,'PhoneticExtensions'))
        elif Devanagar.search(it):
            content=content.replace(it,fnfont(it,'Devanagar'))
        elif Gurmukhi.search(it):
            content=content.replace(it,fnfont(it,'Gurmukhi'))
        elif Oriya.search(it):
            content=content.replace(it,fnfont(it,'Oriya'))
        elif Tamil.search(it):
            content=content.replace(it,fnfont(it,'Tamil'))
        elif Kannada.search(it):
            content=content.replace(it,fnfont(it,'Kannada'))
        elif Tibetan.search(it):
            content=content.replace(it,fnfont(it,'Tibetan'))
        elif Thai.search(it):
            content=content.replace(it,fnfont(it,'Thai'))
        elif UnifiedCanadianAboriginalSyllabics.search(it):
            content=content.replace(it,fnfont(it,'UnifiedCanadianAboriginalSyllabics'))
        elif HangulJamo.search(it):
            content=content.replace(it,fnfont(it,'HangulJamo'))
        elif Hangul.search(it):
            content=content.replace(it,fnfont(it,'Hangul'))
        elif KatakanaPhoneticExtensions.search(it):
            content=content.replace(it,fnfont(it,'KatakanaPhoneticExtensions'))
        elif Halfwidthkatakana.search(it):
            content=content.replace(it,fnfont(it,'Halfwidthkatakana'))
        elif HalfwidthHangul.search(it):
            content=content.replace(it,fnfont(it,'HalfwidthHangul'))
        elif Bopomofo.search(it):
            content=content.replace(it,fnfont(it,'Bopomofo'))
        elif Yi.search(it):
            content=content.replace(it,fnfont(it,'Yi'))
        elif SpacingModifierLetters.search(it):
            content=content.replace(it,fnfont(it,'SpacingModifierLetters'))
        elif SuperscriptsandSubscripts.search(it):
            content=content.replace(it,fnfont(it,'SuperscriptsandSubscripts'))
        elif CombiningDiacriticalMarks.search(it):
            content=content.replace(it,fnfont(it,'CombiningDiacriticalMarks'))
        elif CombiningDiacriticalMarksSupplement.search(it):
            content=content.replace(it,fnfont(it,'CombiningDiacriticalMarksSupplement'))
        elif CombiningDiacriticalMarksforSymbols.search(it):
            content=content.replace(it,fnfont(it,'CombiningDiacriticalMarksforSymbols'))
        elif CJKCompatibilityForms.search(it):
            content=content.replace(it,fnfont(it,'CJKCompatibilityForms'))
        elif LetterlikeSymbols.search(it):
            content=content.replace(it,fnfont(it,'LetterlikeSymbols'))
        elif MathematicalAlphanumericSymbols.search(it):
            content=content.replace(it,fnfont(it,'MathematicalAlphanumericSymbols'))
        elif CJKCompatibility.search(it):
            content=content.replace(it,fnfont(it,'CJKCompatibility'))
        elif BoxDrawing.search(it):
            content=content.replace(it,fnfont(it,'BoxDrawing'))
        elif MiscellaneousTechnical.search(it):
            content=content.replace(it,fnfont(it,'MiscellaneousTechnical'))
        elif NKo.search(it):
            content=content.replace(it,fnfont(it,'NKo'))
        elif Lao.search(it):
            content=content.replace(it,fnfont(it,'Lao'))
        elif Malayalam.search(it):
            content=content.replace(it,fnfont(it,'Malayalam'))
        elif GeometricShapes.search(it):
            content=content.replace(it,fnfont(it,'GeometricShapes'))
        elif Batak.search(it):
            content=content.replace(it,fnfont(it,'Batak'))
        elif Hebrew.search(it):
            content=content.replace(it,fnfont(it,'Hebrew'))
        elif Bengali.search(it):
            content=content.replace(it,fnfont(it,'Bengali'))
        elif Gujarati.search(it):
            content=content.replace(it,fnfont(it,'Gujarati'))
        elif Telugu.search(it):
            content=content.replace(it,fnfont(it,'Telugu'))
        elif Sinhala.search(it):
            content=content.replace(it,fnfont(it,'Sinhala'))
        elif Georgian.search(it):
            content=content.replace(it,fnfont(it,'Georgian'))
        elif Cherokee.search(it):
            content=content.replace(it,fnfont(it,'Cherokee'))
        elif Mongolian.search(it):
            content=content.replace(it,fnfont(it,'Mongolian'))
        elif OpticalCharacterRecognition.search(it):
            content=content.replace(it,fnfont(it,'OpticalCharacterRecognition'))
        elif Arrows.search(it):
            content=content.replace(it,fnfont(it,'Arrows'))
        elif EnclosedAlphabet.search(it):
            content=content.replace(it,fnfont(it,'EnclosedAlphabet'))
        elif unicodeinhelvetica.search(it):
            content=content.replace(it,fnfont(it,'unicodeinhelvetica'))
        elif it in CJKinkaomoji:
            content=content.replace(it,fnfont(it,'CJKinkaomoji'))
        elif it in kaomojibetterinhiragino:
            content=content.replace(it,fnfont(it,'kaomojibetterinhiragino'))
        elif it in kaomojibetterinMSPGothic:
            content=content.replace(it,fnfont(it,'kaomojibetterinMSPGothic'))
        elif kaomojibetterinArialUnicodeMS.search(it):
            content=content.replace(it,fnfont(it,'kaomojibetterinArialUnicodeMS'))
        elif it in kaomojibetterinmeiryo:
            content=content.replace(it,fnfont(it,'kaomojibetterinmeiryo'))
        elif it in kaomojibetterinAppleSymbols:
            content=content.replace(it,fnfont(it,'kaomojibetterinAppleSymbols'))
        elif it in emojikeptassymbols:
            content=content.replace(it,fnfont(it,'emojikeptassymbols'))
    #    elif Phoenician.search(it):
    #        content=content.replace(it,fnfont(it,'Phoenician'))
        elif it == "𐤔" or it == "ꪝ":
            content=content.replace(it,"w")

    inputpath = os.path.splitext(inputfile)
    outputpath = os.path.join(inputpath[0]+'_without_emoji'+inputpath[1])

    #output
    with open(outputpath,'w',encoding='UTF-8')as f2:
        f2.write(content)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-i','--input',help='the input file')
    args = parser.parse_args()
    inputfile = args.input
    delete_emoji(inputfile)
    