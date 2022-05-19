# !/usr/bin/env python3
# Copyright (c) 2022 Institute for Quantum Computing, Baidu Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

r"""
The source file of the state_vector backend.
"""

import paddle
from typing import List, Iterable, Union


def unitary_transformation(
        state: paddle.Tensor, gate: paddle.Tensor, qubit_idx: Union[List[int], int], num_qubits: int
) -> paddle.Tensor:
    r"""The function of unitary transformation in the mode of state vector.

    Args:
        state: The input quantum state.
        gate: The gate that represents the unitary transformation.
        qubit_idx: The indices of the qubits on which the gate is acted.
        num_qubits: The number of the qubits in the input quantum state.

    Returns:
        The transformed quantum state.
    """
    # The order of the tensor in paddle is less than 10.
    higher_dims = state.shape[:-1]
    num_higher_dims = len(higher_dims)
    
    if not isinstance(qubit_idx, Iterable):
        qubit_idx = [qubit_idx]
       
    # generate swap_list
    num_acted_qubits = len(qubit_idx)
    origin_seq = list(range(0, num_qubits))
    seq_for_acted = qubit_idx + [x for x in origin_seq if x not in qubit_idx]
    swapped = [False] * num_qubits
    swap_ops = []
    for idx in range(0, num_qubits):
        if not swapped[idx]:
            next_idx = idx
            swapped[next_idx] = True
            while not swapped[seq_for_acted[next_idx]]:
                swapped[seq_for_acted[next_idx]] = True
                if next_idx < seq_for_acted[next_idx]:
                    swap_ops.append((next_idx, seq_for_acted[next_idx]))
                else:
                    swap_ops.append((seq_for_acted[next_idx], next_idx))
                next_idx = seq_for_acted[next_idx]
    for swap_op in swap_ops:
        shape = higher_dims.copy()
        last_idx = -1
        for idx in swap_op:
            shape.append(2 ** (idx - last_idx - 1))
            shape.append(2)
            last_idx = idx
        shape.append(2 ** (num_qubits - last_idx - 1))
        state = paddle.reshape(state, shape)
        state = paddle.transpose(
            state, list(range(0, num_higher_dims)) + [item + num_higher_dims for item in [0, 3, 2, 1, 4]]
        )
    state = paddle.reshape(state, higher_dims.copy() + [2 ** num_acted_qubits, 2 ** (num_qubits - num_acted_qubits)])
    state = paddle.matmul(gate, state)
    swap_ops.reverse()
    for swap_op in swap_ops:
        shape = higher_dims.copy()
        last_idx = -1
        for idx in swap_op:
            shape.append(2 ** (idx - last_idx - 1))
            shape.append(2)
            last_idx = idx
        shape.append(2 ** (num_qubits - last_idx - 1))
        state = paddle.reshape(state, shape)
        state = paddle.transpose(
            state, list(range(0, num_higher_dims)) + [item + num_higher_dims for item in [0, 3, 2, 1, 4]]
        )

    state = paddle.reshape(state, higher_dims.copy() + [2 ** num_qubits])
    return state
