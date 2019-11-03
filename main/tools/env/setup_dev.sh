#!/bin/bash
#
# Licensed under the Apache License, Version 2.0 (the "License");
# You may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# http://www.apache.org/licenses/LICENSE-2.0OA
#
# Authors:
# - Wen Guan, <wen.guan@cern.ch>, 2019


CurrentDir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
ToolsDir="$( dirname "$CurrentDir" )"
RootDir="$( dirname "$ToolsDir" )"
CondaDir=${RootDir}/../.conda/iDDS

echo 'Root dir: ' $RootDir
export IDDS_HOME=$RootDir

conda activate $CondaDir
#export PYTHONPATH=${IDDS_HOME}/lib:$PYTHONPATH
