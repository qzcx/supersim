/*
 * Licensed under the Apache License, Version 2.0 (the 'License');
 * you may not use this file except in compliance with the License.
 * See the NOTICE file distributed with this work for additional information
 * regarding copyright ownership. You may obtain a copy of the License at
 *
 *  http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
#ifndef STATS_TRAFFICLOG_H_
#define STATS_TRAFFICLOG_H_

#include <fio/OutFile.h>
#include <json/json.h>
#include <prim/prim.h>

#include "event/Component.h"

class TrafficLog {
 public:
  explicit TrafficLog(Json::Value _settings);
  ~TrafficLog();
  void logTraffic(const Component* _device, u32 _inputPort, u32 _inputVc,
                  u32 _outputPort, u32 _outputVc, u32 _flits);

 private:
  fio::OutFile* outFile_;
};

#endif  // STATS_TRAFFICLOG_H_
