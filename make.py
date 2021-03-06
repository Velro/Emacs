#!/usr/bin/python
import glob
import os
import sys
import tempfile

#recursive glob - looks for all files below src_path that match 'flt' and aren't in 'excl'
def rglob(src_path, flt, excl=[]):
    import fnmatch
    matches = []
    for root, dirnames, filenames in os.walk(src_path):
        for filename in fnmatch.filter(filenames, flt):
            include_it = True
            fullpath = os.path.join(root, filename)
            for exclusion in excl:
                if fnmatch.fnmatch(fullpath, exclusion):
                    include_it = False
                    break
            if include_it:
                matches.append(fullpath)
				
    print src_path
    return matches

def get_main_files(filedir, inexcl):
    excl = list(inexcl)
    excl.append("*/Lib/*")
    excl.append("*/NGui/*")
    files = []
    files += rglob(os.path.join(filedir, "Assets/Scripts"), "*.cs", excl)
    files += rglob(os.path.join(filedir, "Assets/Standard Assets/Image Effects (Pro Only)"), "*.cs", excl)
    print "asdf"
    return files
    
def get_lib_files(filedir, inexcl):
    excl = list(inexcl)
    excl.append("*/Build/*")
    files = []
    files += rglob(os.path.join(filedir, "Assets/Lib"), "*.cs", excl)
    files += rglob(os.path.join(filedir, "Assets/NGui"), "*.cs", excl)
    return files

#if entry 'match' is in 'file_list', swap it with 'swap'
def swap_file(file_list, match, swap):
    if match!=None and swap!=None:
        for c1 in xrange(len(file_list)):
            val = file_list[c1]
            if os.path.abspath(val)==os.path.abspath(match):
                file_list[c1] = swap
                return True
        
    return False

#Compile all files 'files' into a dll 'filename', including the libraries in 'inlibs' 
def compile_files(files, filename, inlibs=None): 
    files_as_string = ""

    for file in files:
        files_as_string += os.path.normpath("\"" + file + "\" ")
    
    # print(files_as_string)
    libs = []
    if inlibs != None:
        libs=list(inlibs)

    compile_command = ""
    if platform.system()=="Windows":
        import uuid
        compile_command = r'C:\windows\Microsoft.NET\Framework\v4.0.30319\csc.exe /noconfig /nologo /warn:4 /debug:+ /debug:full /optimize- /nowarn:0169 /fullpaths /utf8output /t:library'
        # tmp_name = uuid.uuid4()#"__tmp.rsp"
        
        tmp_name = None
        with tempfile.NamedTemporaryFile("w+", delete=False) as tmp:
            tmp_name = tmp.name
            tmp.write(r'"/out:%s" '%(filename) + "\r\n")
            tmp.write(r'"/r:C:\Program Files (x86)\Reference Assemblies\Microsoft\Framework\.NETFramework\v4.0\System.dll"'+'\r\n')
            tmp.write(r'"/r:C:\Program Files (x86)\Reference Assemblies\Microsoft\Framework\.NETFramework\v4.0\System.Xml.dll"'+'\r\n')
            tmp.write(r'"/r:C:\Program Files (x86)\Reference Assemblies\Microsoft\Framework\.NETFramework\v4.0\System.Core.dll"'+'\r\n')
            tmp.write(r'"/r:C:\Program Files\Unity\Editor\Data\Managed\UnityEngine.dll"'+'\r\n') 
            tmp.write(r'"/r:C:\Program Files\Unity\Editor\Data\Managed\UnityEditor.dll"'+'\r\n')
            tmp.write(r'"/r:C:\Program Files\Unity\Editor\Data\UnityExtensions\Unity\GUISystem\UnityEngine.UI.dll"'+'\r\n')
            for l in libs:
                tmp.write('"/r:%s"\r\n' %os.path.normpath(l))
            tmp.write("/define:DEBUG;TRACE;UNITY_STANDALONE;ENABLE_MICROPHONE;ENABLE_IMAGEEFFECTS;ENABLE_WEBCAM;ENABLE_AUDIO_FMOD;ENABLE_NETWORK;ENABLE_MONO;ENABLE_PHYSICS;ENABLE_TERRAIN;ENABLE_CACHING;ENABLE_SUBSTANCE;ENABLE_GENERICS;ENABLE_CLOTH;ENABLE_MOVIES;ENABLE_AUDIO;ENABLE_WWW;ENABLE_SHADOWS;ENABLE_DUCK_TYPING;UNITY_4_0_1;UNITY_4_0;UNITY_STANDALONE_WIN;ENABLE_PROFILER;UNITY_EDITOR\r\n")
            tmp.write(files_as_string)
        print compile_command+" @"+tmp_name
        sts = subprocess.call(compile_command+" @" + tmp_name, shell=True)
        os.remove(tmp_name)

UnityFolder = ""

def setupUnityFolder():
    if platform.system()=="Windows":
        platformRoot = r"C:/Program Files/Unity"
    else:
        platformRoot = r"/Applications"

    global UnityFolder
    UnityFolder = "%s/5.1.1f1"%platformRoot

    os.environ["MONO_PATH"] = "%s/Unity.app/Contents/Frameworks/Mono/lib/mono/unity"%UnityFolder
            
        

if __name__ == '__main__':
    #params are fast, working_dir, exclude_file, extra_file
    import platform
    import subprocess

    setupUnityFolder()
    
    compile_extension = "Build"
    fastCompile = False

    excludes = ["*.#*"]
    filedir = os.getcwd()
    exclude_file = None
    extra_file = None

    if len(sys.argv)>1:
        if sys.argv[1]=="fast":
            fastCompile = True

    if len(sys.argv)>2:
        if sys.argv[2]!=".":
            filedir = sys.argv[2]

    if len(sys.argv)>3:
        compile_extension="Flymake"
        exclude_file = sys.argv[3]

    if len(sys.argv)>4:
        extra_file = sys.argv[4]
    
    libfilelist = []
    #libfilelist.append('%s/Assets/Scripts/Plugins/JsonFX/JsonFx.Json.dll'%filedir) 

    buildTemp = "%sBuildTemp"%(filedir)
    if not os.path.exists(buildTemp):
        os.makedirs(buildTemp)

    
    # Split this into a single lib for our static stuff
    liboutfile = "%s/LibBuild.dll"%(buildTemp)
    libfiles = get_lib_files(filedir, excludes)

    swap_is_in_lib = swap_file(libfiles, exclude_file, extra_file)
    
    if fastCompile and swap_is_in_lib:
        print "file to test is in the precompiled bit - reverting to slow compile"
        fastCompile = False
            
    if not fastCompile:
        print "Building the libs"
        compile_files(libfiles, liboutfile, libfilelist)
    libfilelist.append(liboutfile)

    print "Building the game"
    main_files = get_main_files(filedir, excludes)
    swap_file(main_files, exclude_file, extra_file)
    outfile = "%s/MainBuild%s.dll"%(buildTemp, compile_extension)
    compile_files(main_files, outfile, libfilelist)
